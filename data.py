import sys
import os
import json
from jsonConfig import jsonFile
import site

import sys
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

"""
Library to work with fbx data.
"""
class fbxScene(object):
    def __init__(self, fileName):
        self.fileName = fileName
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
        lTmpStr=""
        self.startTime = int(str(lStart.GetTimeString(lTmpStr, 10).replace('*','')))
        self.endTime = int(str(lEnd.GetTimeString(lTmpStr, 10).replace('*','')))

        self.indexDict = self.getIndexDict()
        #print str(self.startTime) + " " + str(self.endTime)

        self.animEval = self.lScene.GetAnimationEvaluator()

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

    def getStartTime(self):
        return self.startTime

    def getEndTime(self):
        return self.endTime

class baseData (object):
    def __init__(self, jsonNode):
        self.__dict__ = jsonNode


class fbxData(baseData):
    """
    Turns json dict into this object's attributes.
    """
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode)
        self.fbxFiles = self.getFbxFiles()
        self.fbxScenes = self.getFbxScenes()

    def getFbxFiles(self):
        files = []
        if hasattr(self, 'dir'):
            for f in os.listdir(self.dir):
                if f.endswith('.fbx'):
                    files.append(self.dir+'/'+f)
        return files

    def getFbxScenes(self):
        fbxScenes = []
        for f in self.fbxFiles:
            fbxScenes.append(fbxScene(f))
        return fbxScenes


class dataManager(object):
    """
    Generic class used in different types of 'data managers'.
    """
    def __init__(self, dataType):
        #use jsonConfig module hack to get json config file
        jsonFileObj = jsonFile()
        jsonFilePath = jsonFileObj.getJsonFile()
        self.jsonNodes = json.loads(open(jsonFilePath).read())
        #encapsulate fbxs json data into fbx objects
        self.dataObjects = self.getObjects(self.jsonNodes[dataType])


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

    def getObjects(self, jsonNodes):
        dataObjects = []
        for d in jsonNodes:
            dataObj = fbxData(d)
            if dataObj.name == "config":
                self.config = dataObj
            else:
                dataObjects.append(dataObj)   
        return dataObjects   


class nnData(object):
    """
    Container for nn data.
    """
    def __init__(self,lineArray):
        self.lineArray = lineArray

    def write(self,filePath):
        dataFile = open(filePath,'w')
        for l in self.lineArray:
            dataFile.write("%s\n" % l)

    def printData(self):
        for l in self.lineArray:
            print l


class fbxManager(dataManager):
    """
    Manages fbx groups, for organized directories of fbx files.
    """
    def __init__(self, dataType):
        dataManager.__init__(self, dataType) 

    def getNnDataObj(self,nnConfigObj):
        lineArray = []
        for fbxGroupName in nnConfigObj.fbxGroups:
            g = self.getObject(fbxGroupName)
            for scene in g.getFbxScenes():
                for frame in range(scene.startTime,scene.endTime+1):
                    line = []
                    for jointDataList in nnConfigObj.input:
                        print "fbxGroup: %s fbxScene: %s frame: %s joint: %s transformPart: %s space: %s" % \
                                    (fbxGroupName,scene.fileName,int(frame),jointDataList[0],\
                                    jointDataList[1],jointDataList[2])
                        
                        #each jointName returns a list with elem 0 as transform component
                        #type (ie. position or rotation), and elem 1 specifies global or
                        #local offset from parent
                        if jointDataList[1]=="pos":

                            if jointDataList[2]=="world":
                                line = line + list(scene.getGlobalPos(jointDataList[0],frame))
                            elif jointDataList[2]=="local":
                                line = line + list(scene.getLocalPos(jointDataList[0],frame))
                        
                        elif jointDataList[1]=="rot":
                            if jointDataList[2]=="world":
                                line = line + list(scene.getGlobalRot(jointDataList[0],frame))
                            elif jointDataList[2]=="local":
                                line = line + list(scene.getLocalRot(jointDataList[0],frame))

                    #convert line array to string. 
                    lineArray.append(', '.join(str(l) for l in line))
        
                    
        #return nnData(['a','b'])
        return nnData(lineArray)


class nnDataConfigurations(dataManager):
    """
    Manages nn configurations
    """
    def __init__(self, dataType):
        dataManager.__init__(self, dataType)

        



