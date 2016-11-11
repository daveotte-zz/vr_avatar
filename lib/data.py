import os
import json
import site
import random
import sys
import re
import matrixUtil as mx
import operations as op
from path import Path

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


def camel2Title(camel):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', camel).title()



#return abs path to a json file. Why do I have to do this?


def getJsonFile():
    '''
    Return abs path to json files
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
        self.dataObjects = self.getObjects(json.loads(open(getJsonFile()).read()))      
        
    def getObjects(self, jsonNodes):
        dataObjects = []
        for d in jsonNodes[self.dataType]:
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


class fbxDataManager(dataManager):
    """
    Manages fbx groups, for organized directories of fbx files.
    """
    def __init__(self, dataType):
        dataManager.__init__(self, dataType) 
        
    def destroy(self):
        for obj in self.dataObjects:
            obj.destroy()

    def getJointTransformAtFrame(self, transformList, scene, frame):
        """
        Return FBX mx4 for a joint within an fbx scene, at a specificed time.
        """
        # elem 0 is joint name
        # elem 1 specifies global or local offset from parent
        if transformList[1]=="world":
            return scene.getGlobalTransform(transformList[0],frame)
        elif transformList[1]=="local":
            return scene.getLocalTransform(transformList[0],frame)

    def getFbxFiles(self):
        fList = []
        for f in self.dataObjects:
            fList = flist + f.getFbxFiles()
        return fList


class fbxData(baseData):
    """
    Append specific methods to deal with fbx data.
    """
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode)
        self.fbxFiles = self.getFbxFiles()
        self.fbxScenes = self.getFbxScenes()

    def destroy(self):
        for scene in self.fbxScenes:
            scene.destroy()

    def getFbxFiles(self):
        files = []
        if hasattr(self, 'dir'):
            for f in os.listdir(self.dir):
                if f.endswith('.fbx'):
                    files.append(self.dir+'/'+f)
        return files

    def getFbxFileNames(self):
        names = []
        for file in self.getFbxFiles():
            names.append(Path(file).basename())
        return names

    def getFbxScenes(self):
        fbxScenes = []
        for f in self.fbxFiles:
            fbxScenes.append(fbxScene(f))
        return fbxScenes




class fbxScene(object):
    """
    Library to work with an fbx scene (a .fbx file).
    """
    def __init__(self, fileName):
        self.fileName = fileName
        self.initialized = False
        self.basename = Path(self.fileName).basename()

    def initialize(self):
        self.time = FbxTime()
        self.lSdkManager, self.lScene = InitializeSdkObjects()
        lResult = LoadScene(self.lSdkManager, self.lScene, self.fileName)
        lAnimStack = self.lScene.GetSrcObject(FbxAnimStack.ClassId, 0)
        
        #set fps to 24, even though these fbx files are at 30.
        #I'm doing this since Blender and Maya default to 24
        self.time.SetGlobalTimeMode(11)       
        lTs = lAnimStack.GetLocalTimeSpan()

        lStart = lTs.GetStart()
        lEnd   = lTs.GetStop()
        lTmpStr="frank"
        self.startTime = int(str(lStart.GetTimeString(lTmpStr, 10).replace('*','')))
        self.endTime = int(str(lEnd.GetTimeString(lTmpStr, 10).replace('*','')))

        self.indexDict = self.getIndexDict()

        self.animEval = self.lScene.GetAnimationEvaluator()
        self.initialized = True

    def getIndexDict(self):
        """
        Create dictionary lookup table with joint name 
        as keys, and index number by value
        """
        indexDict = {}
        for i in range(self.lScene.GetNodeCount()):
            indexDict[self.lScene.GetNode(i).GetName()]=i
        return indexDict

    def getNodeIndexByName(self,jointName):
        return self.getIndexDict()[jointName]

    def getNode(self,jointName):
        """
        Return FbxNode by joint name.
        """
        return self.lScene.GetNode(self.getNodeIndexByName(jointName))

    def getNpGlobalTransform(self, jointName, time=0):
        return mx.fbxMxtoNumpyMx(self.getGlobalTransform(jointName,time))

    def getNpLocalTransform(self, jointName, time=0):
        return mx.fbxMxtoNumpyMx(self.getLocalTransform(jointName,time))

    def getGlobalTransform(self, jointName, time=0):
        """
        Return transform of specificied joint node,
        at the specified time.
        """
        self.time.SetFrame(time)
        return self.animEval.GetNodeGlobalTransform(self.getNode(jointName),self.time)
 
    def getLocalTransform(self, jointName, time=0):
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


class nnData(object):
    """
    Composes nn data using fbxDataManager and an nnConfig objects.
    """
    def __init__(self,fbxDataManager, nnConfig):
        self.nnConfig = nnConfig
        self.fbxDataManager = fbxDataManager
        self.data = self.setData()

    def setData(self):
        data = []
        for transforms in self.transforms:
            operation = getattr(op, self.nnConfig.method)
            #list of tranforms serves as arguments to 'operation'
            inputLinePortion, outputLinePortion = operation(transforms)
            line = inputLinePortion + outputLinePortion
            data.append(line)
        self.inputStart = 0
        self.inputEnd = len(inputLinePortion)
        self.outputStart = self.inputEnd  
        self.outputEnd = self.outputStart + len(outputLinePortion)            

        return data

    @property
    def fbxDataObjects(self):
        """
        Return all the fbx data Groups objects that will be
        used per the nnConfig object.
        """
        fbxGroupObjects = []
        for fbxGroupName in self.nnConfig.fbxGroups:
            print 'Getting fbxGroup: %s '%(fbxGroupName)
            fbxGroupObjects.append(self.fbxDataManager.getObject(fbxGroupName))
        return fbxGroupObjects

    @property
    def fbxScenes(self):
        """
        Return all the fbx scenes that will be
        used per the nnConfig object.
        """
        fbxScenes = []
        for fbxDataObj in self.fbxDataObjects:
            fbxScenes.append(fbxDataObj.getFbxScenes())

    @property
    def fbxFiles(self):
        """
        Return a list of all the files used
        per nnConfigObj
        """
        fList = []
        for g in self.fbxDataObjects:
            fList = fList + g.getFbxFileNames()
        return fList

    @property
    def fbxFileNames(self):
        """
        Return a list of all the names of all
        the files used per nnConfigObj.
        """
        names = []
        for file in self.fbxFiles:
            names.append(Path(file).basename())
        return names

    @property
    def fbxScenes(self):
        """
        Return a list of all the fbx scenes used
        per nnConfigObj
        """
        fList = []
        for g in self.fbxDataObjects:
            fList = fList + g.getFbxScenes()
        return fList
    #TODO - be consistent about using numpy array FOR EVERYTHING.
    #There are fbx mx4's, python lists, and numpy arrays. I should
    #convert fbx mx4's to numpy arrays, and then never turn back.
    @property
    def transforms(self):
        """
        A list of numpy transform lists that will
        be used per the nnConfig object.
        """
        bigTransformList = []
        for scene in self.fbxScenes:
            scene.initialize()
            bigTransformList = bigTransformList + self.getSceneTransforms(scene)
        return bigTransformList

    def getSceneTransforms(self,scene):
        scene.initialize()
        sceneTransforms = []
        for frame in range(scene.startTime,scene.endTime+1):
            sceneTransforms.append(self.getSceneTransformsAtFrame(scene,frame))
        return sceneTransforms
    
    def getSceneTransformsAtFrame(self,scene,frame):
        scene.initialize()
        transformsAtFrame = []
        for x in self.nnConfig.transforms:
            #extract transforms we will process
            transformsAtFrame.append(mx.fbxMxtoNumpyMx(self.fbxDataManager.getJointTransformAtFrame(x,scene,int(frame))))
        return transformsAtFrame

    def write(self,filePath):
        dataFile = open(filePath,'w')
        for line in self.data:
            #convert line to string. 
            l = ', '.join(str(ln) for ln in line)
            dataFile.write("%s\n" % l)
        self.file = filePath

    def printData(self):
        for l in self.data:
            print l



'''
Why make these classes? To avoid writing a many
lines of code to specify we want the base class 'dataManager'
instead of the subclass, here names 'nnConfigDataManager'.
'''
class nnConfigDataManager(dataManager):
    def __init__(self, dataType):
        dataManager.__init__(self, dataType) 
 
class nnConfigData(baseData):
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode) 


