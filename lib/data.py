from multiprocessing import Process

import os
import json
import site
import random
import sys
import re
import matrixUtil as mxUtil
import operations as op
from path import Path
from threading import Thread

sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from DisplayGlobalSettings  import *
from DisplayHierarchy       import DisplayHierarchy
from DisplayMarker          import DisplayMarker
from DisplayMesh            import DisplayMesh
from DisplayUserProperties  import DisplayUserProperties
from DisplayPivotsAndLimits import DisplayPivotsAndLimits
from DisplaySkeleton        import DisplaySkeleton
from DisplayNurb            import DisplayNurb
from DisplayPatch           import DisplayPatch
from DisplayCamera          import DisplayCamera
from DisplayLight           import DisplayLight
from DisplayLodGroup        import DisplayLodGroup
from DisplayPose            import DisplayPose
from DisplayAnimation       import DisplayAnimation
from DisplayGenericInfo     import DisplayGenericInfo

from FbxCommon import *
import numpy as np
from keras.models import Sequential
from keras.models import model_from_json

def getJsonFile():
    '''
    Return abs path to json file.
    '''
    return os.path.dirname(__file__) + '/config.json'

class baseData(object):
    def __init__(self, jsonNode):
        self.__dict__ = jsonNode

    @property 
    def title(self):
        return camel2Title(self.name)

class dataManager(object):
    """
    Base class. Converts json nodes python objects with json node attrs as properties.
    Methods added to make it wasy to access/manipulate the json data.
    'dataType' corresponds to json node name, AND object class type.
    """
    def __init__(self, dataType):
        self.dataType = dataType
        print "Getting Data type: %s"%dataType
        self.dataObjects = self.getObjects(json.loads(open(getJsonFile()).read()))      
        
    def getObjects(self, jsonNodes):
        dataObjects = []
        for d in jsonNodes[self.dataType]:
            #data type name used to find class name
            dataObj = globals()[self.dataType](d)
            if dataObj.name == "config":
                self.config = dataObj
            else:
                dataObjects.append(dataObj)   
        return dataObjects 

    def getObjByName(self, name): 
        for obj in self.dataObjects:
            if name == obj.name:
                return obj
        return None

    def getObject(self, objectIndexOrName):
        if type(objectIndexOrName) == int:
            return self.getObjByIndex(objectIndexOrName)
        else:
            return self.getObjByName(objectIndexOrName)
            
    def getObjByIndex(self, index): 
        for obj in self.dataObjects:
            if index == obj.index:
                return obj
        return None


class fbxManager(dataManager):
    """
    Manages fbx data stored on disk in organized directories(asfbx files).
    """
    def __init__(self, groupIndices, dataType="fbxGroup"):
        dataManager.__init__(self, dataType) 
        self.groupIndices = groupIndices
        
    def destroy(self):
        for obj in self.dataObjects:
            obj.destroy()
#appears not to be used
#    def getFbxFiles(self):
#        fList = []
#        for f in self.dataObjects:
#            fList = flist + f.getFbxFiles()
#        return fList

    @property 
    def fbxScenes(self):
        return self.fbxScenesByFbxGroupIndices(self.groupIndices)

    def fbxScenesByFbxGroupIndices(self,groupIndices):
        fbxSceneObjects = []
        for g in self.fbxGroupObjectsByIndices(groupIndices):
            fbxSceneObjects = fbxSceneObjects + g.fbxScenesInGroup()
        return fbxSceneObjects

    def fbxGroupObjectsByIndices(self,groupIndices):
        """
        Return all the fbx data Groups objects that will be
        used per the nnConfig object.
        """
        fbxGroupObjects = []
        for fbxGroupIndex in groupIndices:
            print 'Getting fbxGroup: %s '%(fbxGroupIndex)
            fbxGroupObjects.append(self.getObject(fbxGroupIndex))
        return fbxGroupObjects


class fbxGroup(baseData):
    """
    Append specific methods to deal with fbx data.
    """
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode)

    def destroy(self):
        for scene in self.fbxScenes:
            scene.destroy()

    def fbxFilesInGroup(self):
        files = []
        if hasattr(self, 'dir'):
            for f in os.listdir(self.dir):
                if f.endswith('.fbx'):
                    files.append(self.dir+'/'+f)
        return files

    def fbxFileNamesInGroup(self):
        names = []
        for file in self.fbxFilesInGroup()():
            names.append(Path(file).basename())
        return names

    def fbxScenesInGroup(self):
        fbxScenesInGroup = []
        for f in self.fbxFilesInGroup():
            fbxScenesInGroup.append(fbxScene(f))
        return fbxScenesInGroup



class joint(object):
    def __init__(self,name='RootNode'):
        self.name = name
        self.children = [False]


class fbxScene(object):
    """
    Library to work with an fbx scene (a .fbx file).
    """
    def __init__(self, fileName):
        self.fileName = fileName
        self.needsInitializing = True
        self.basename = Path(self.fileName).basename()

    def initialize(self):
        if self.needsInitializing:
            print "Initializing: %s"%(self.fileName)
            self.time        = FbxTime()
            self.lSdkManager, self.lScene   = InitializeSdkObjects()
            lResult                         = LoadScene(self.lSdkManager, self.lScene, self.fileName)
            self.needsInitializing          = False
            
            lAnimStack                      = self.lScene.GetSrcObject(FbxAnimStack.ClassId, 0)
            
            #set fps to 24, even though these fbx files are at 30.
            #I'm doing this since Blender and Maya default to 24
            self.time.SetGlobalTimeMode(11)       
            lTs                             = lAnimStack.GetLocalTimeSpan()
            lStart                          = lTs.GetStart()
            lEnd                            = lTs.GetStop()
            lTmpStr                         = "something"
            self.start                      = int(str(lStart.GetTimeString(lTmpStr, 10).replace('*','')))
            self.end                        = int(str(lEnd.GetTimeString(lTmpStr, 10).replace('*','')))
            self.animEval                   = self.lScene.GetAnimationEvaluator()
            self.jointNameAndIndexDict      = self.getJointNameAndIndexDict()
            self.jointRoot                  = self.getNode('hip')
            self.makeSkeletonNodeNameList()
            


    @property
    def startTime(self):
        self.initialize()
        return self.start

    @property
    def endTime(self):
        self.initialize()
        return self.end

    def getJointNameAndIndexDict(self):
        """
        Create dictionary lookup table with joint name 
        as keys, and index number by value
        """
        self.initialize()
        indexDict = {}
        for i in range(self.lScene.GetNodeCount()):
            indexDict[self.lScene.GetNode(i).GetName()]=i
        return indexDict
    
    def makeSkeletonNodeNameList(self):
        """
        Create list of joints in skeleton. Walk hierarchy
        from specified root node to make the list.
        """       
        self.skeletonNodeNameList = []
        self.walkHierarchy(self.jointRoot)

    def walkHierarchy(self, fbxNode):
        """
        Walk hierarchy to draw lines from parent to children.
        """
        self.skeletonNodeNameList.append(fbxNode.GetName())
        for i in range(fbxNode.GetChildCount()):
                self.walkHierarchy(fbxNode.GetChild(i))


    def getFbxNodeNpTransformAtFrame(self, jointName, frame, transformSpace="world"):
        """
        Return numpy mx4 for a node within the fbx scene at a specificed time.
        """
        if transformSpace=="world":
            return mxUtil.fbxMxtoNumpyMx(self.getGlobalTransform(jointName, frame))
        elif transformSpace=="local":
            return mxUtil.fbxMxtoNumpyMx(self.getLocalTransform(jointName, frame))
        else:
            print "Need to specify 'world' or 'local'."

    def getNodeIndexByName(self,jointName):
        self.initialize()
        return self.jointNameAndIndexDict[jointName]

    def getNode(self,jointName):
        """
        Return FbxNode by joint name.
        """
        self.initialize()
        return self.lScene.GetNode(self.getNodeIndexByName(jointName))

    def getNpGlobalTransform(self, jointName, time=0):
        return mxUtil.fbxMxtoNumpyMx(self.getGlobalTransform(jointName,time))

    def getNpLocalTransform(self, jointName, time=0):
        return mxUtil.fbxMxtoNumpyMx(self.getLocalTransform(jointName,time))

    def getGlobalTransform(self, jointName, time=0):
        """
        Return transform of specificied joint node,
        at the specified time.
        """
        self.initialize()
        self.time.SetFrame(time)
        return self.animEval.GetNodeGlobalTransform(self.getNode(jointName),self.time)
 
    def getLocalTransform(self, jointName, time=0):
        self.initialize()
        self.time.SetFrame(time)
        return self.animEval.GetNodeLocalTransform(self.getNode(jointName),self.time)

    def getGlobalPos(self,jointName,time=0):
        """
        Return a list of 3 numbers to represent local position component
        of given matrix.
        """
        return self.v4Tov3(self.getGlobalTransform(jointName,time).GetRow(3))

    def getLocalPos(self,jointName,time=0):
        """
        Return a list of 3 numbers to represent global position component
        of given matrix.
        """
        return self.v4Tov3(self.getLocalTransform(jointName,time).GetRow(3))
 
    def getGlobalRot(self,jointName,time=0):
        """
        Return a list of 9 numbers to represent global Mx3 rotation extracted
        from joint's global Mx4 transform.
        """
        return self.extractRotAsList(self.getGlobalTransform(jointName,time))
 
    def getLocalRot(self,jointName,time=0):
        """
        Return a list of 9 numbers to represent global Mx3 rotation extracted
        from joint's global Mx4 transform.
        """
        return self.extractRotAsList(self.getLocalTransform(jointName,time))

    def extractRotAsList(self, mx4):
        """
        Extract rot/scale from mx4 as list of 9 numbers.
        """
        return  self.v4Tov3(mx4.GetRow(0)) + \
                self.v4Tov3(mx4.GetRow(1)) + \
                self.v4Tov3(mx4.GetRow(2))

    def v4Tov3 (self,v4):
        v3=[]
        v3.append(v4[0])
        v3.append(v4[1])
        v3.append(v4[2]) 
        return v3      

    def destroy(self):
        if self.initialized:
            print 'destroy'
            self.lSdkManager.Destroy()
        self.needsInitializing = True

class nnData(object):
    """
    Composes nn data using fbxManager and an nnConfig objects.
    """
    def __init__(self,nnConfig,fbxScenes):
        self.nnConfig = nnConfig
        self.fbxScenes = fbxScenes
        
        operationClass = getattr(op, self.nnConfig.method)
        self.operation = operationClass()
        
        self.loadModel()
        
        self.setData()

    def setData(self):
        data = []
        for transforms in self.extractedTransforms():
            inputLinePortion, outputLinePortion = self.operation.operate(transforms)
            line = inputLinePortion + outputLinePortion
            data.append(line)
        self.inputStart = 0
        self.inputEnd = len(inputLinePortion)
        self.outputStart = self.inputEnd  
        self.outputEnd = self.outputStart + len(outputLinePortion)    
        self.data = data

    def loadModel(self):
        if self.nnConfig.readNnFile.isfile() and self.nnConfig.readWeightsFile.isfile():
            print "Loading model: %s and %s"%(self.nnConfig.readNnFile, self.nnConfig.readWeightsFile)
            jsonFile = open(self.nnConfig.readNnFile,'r')
            jsonString = jsonFile.read().replace('\n', '')
            model = model_from_json(jsonString)
            model.load_weights(self.nnConfig.readWeightsFile)
            self.model =  model 
        else:
            self.model = Sequential()


        
    def extractedTransforms(self):
        """
        A list of numpy mx4 lists that will
        be used per the nnConfig object.
        """
        bigTransformList = []
        for scene in self.fbxScenes:
            bigTransformList =  bigTransformList + self.extractedTransformsOverFrameRange(scene,\
                                                                                scene.startTime,\
                                                                                scene.endTime+1)
        return bigTransformList

    def extractedTransformsOverFrameRange(self,scene,start,end):
        sceneTransforms = []
        for frame in range(start, end+1):
            sceneTransforms.append(self.extractedTransformsAtFrame(scene,frame))
        return sceneTransforms
    
    def extractedTransformsAtFrame(self,scene,frame):
        """
        List of numpy mx4 lists. Numpy mx4 list is for each joint specified in nn configuration.
        """
        transformsAtFrame = []
        for jointNameAndTransformType in self.nnConfig.transforms:
            #extract transforms we will process
            transformsAtFrame.append(scene.getFbxNodeNpTransformAtFrame \
                                                            (jointNameAndTransformType[0],\
                                                            frame,\
                                                            jointNameAndTransformType[1]))
        return transformsAtFrame

    def drawExtractedTransformsAtFrame(self,scene,frame,transformScale):
        for mx in self.extractedTransformsAtFrame(scene,frame):
            mxUtil.drawMx(mx,transformScale)

    def drawPredictedAtFrame(self,scene,frame):
        inputArray, outputArray = self.operation.operate(self.extractedTransformsAtFrame(scene,frame))
        predictedOutputArray = self.model.predict_on_batch(np.array([inputArray]))
        self.operation.predict(predictedOutputArray[0])
        self.operation.drawPredict()

    def drawRecomposeAtFrame(self,scene,frame):
        inputArray, outputArray = self.operation.operate(self.extractedTransformsAtFrame(scene,frame))
        predictedOutputArray = self.model.predict_on_batch(np.array([inputArray]))
        self.operation.recompose(predictedOutputArray[0])
        self.operation.drawRecompose()

    def drawManipulatedTransformsAtFrame(self,scene,frame,transformScale):
        self.operation.operate(self.extractedTransformsAtFrame(scene,frame))
        self.operation.transformScale = transformScale
        self.operation.draw()

    def write(self):
        dataFile = open(self.nnConfig.outputCsvFileName,'w')
        for line in self.data:
            #convert line to string. 
            l = ', '.join(str(ln) for ln in line)
            dataFile.write("%s\n" % l)

    def printData(self):
        for l in self.data:
            print l

class transformsFilesManager(dataManager):
    def __init__(self, dataType):
        dataManager.__init__(self, dataType) 
 
class transformsFiles(baseData):
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode) 
        self.transforms = [line.rstrip('\n') for line in open(self.fileName)]
        self.basename = Path(self.fileName).basename()
        self.start = 0
        self.end = len(self.transforms)

    def drawAtFrame(self,frame,transformScale):
        mxUtil.drawMx(mxUtil.listToNumpyMx(self.transforms[frame]),transformScale)




'''
Why make these classes? To avoid writing a many
lines of code to specify we want the base class 'dataManager'
instead of the subclass, here named 'nnConfigDataManager'.
'''
class nnConfigDataManager(dataManager):
    def __init__(self, configNames, dataType="nnConfigData"):
        dataManager.__init__(self, dataType) 
        self.nnConfigs = self.nnConfigsByConfigName(configNames)
    
    def nnConfigsByConfigName(self,configNames):
        nnConfigs = []
        for configName in configNames:
            nnConfigs.append(self.getObject(configName))
        return nnConfigs 

class nnConfigData(baseData):
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode) 
        self.setUpLoadPaths()

    def setUpLoadPaths(self):
        pathBase = self.logDir + "/" + self.name + "/trial_"
        self.checkDir(pathBase,0)

        self.weightsFileBaseName = self.name+".h5"
        self.nnFileBaseName = self.name+".json"

        self.writeWeightsFile = self.writeDir+"/"+self.weightsFileBaseName
        self.writeNnFile = self.writeDir+"/"+self.nnFileBaseName
        self.readWeightsFile = self.readDir+"/"+self.weightsFileBaseName
        self.readNnFile = self.readDir+"/"+self.nnFileBaseName

        self.configFile = "/home/daveotte/work/vr_avatar/lib/config.json"
        self.writeConfigFile = self.writeDir+"/config.json"

        self.operationsFile = "/home/daveotte/work/vr_avatar/lib/operations.py"
        self.writeOperationsFile = self.writeDir+"/operations.py"


        self.writeLogFile = self.writeDir+"/"+self.name+"_log.txt"

        print "Setting write file: %s"%(self.writeWeightsFile)
        print "Setting read file: %s"%(self.readWeightsFile)
        
    def checkDir(self,pathBase,i):
        suffix = '%03d'%i
        logDir = Path(pathBase+str(suffix))
        nextId = i+1
        prevId = i-1
        print "Checking isdir: " + str(logDir.abspath())
        if os.path.isdir(str(logDir.abspath())):
            self.checkDir(pathBase,nextId)
        else:
            self.writeDir = logDir.makedirs()  
            suffix = '%03d'%prevId  
            self.readDir = Path(pathBase+str(suffix))
            #if this is dir 0 (the first trial ever), then we share the same read/write dir
            if not self.readDir.isdir():   
                self.readDir = self.writeDir






        #is the logDir there? No? then make it.
        #yes, then is nnConfig.name0 there? no, then make it, and make it both read and write dir
        #else      is nnConfig.name1 there? yes
                #is nnConfig.name2 there? yes
                #is nnConfig.name3 there? no, then name2 is read dir, and make name3 as write dir

def camel2Title(camel):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', camel).title()
