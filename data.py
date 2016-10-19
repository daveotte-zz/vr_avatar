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
        lGlobalSettings = self.lScene.GetGlobalSettings()
        lTs = lGlobalSettings.GetTimelineDefaultTimeSpan()
        lStart = lTs.GetStart()
        lEnd   = lTs.GetStop()
        lTmpStr=""
        self.startTime = int(str(lStart.GetTimeString(lTmpStr, 10).replace('*','')))
        self.endTime = int(str(lEnd.GetTimeString(lTmpStr, 10).replace('*','')))

        self.indexDict = self.getIndexDict()



    def getIndexDict(self):
        indexDict = {}
        for i in range(self.lScene.GetNodeCount()):
            indexDict[self.lScene.GetNode(i).GetName()]=i
        return indexDict

    def getNode(self,nodeName):
        return self.lScene.GetNode(self.indexDict[nodeName])

    def getGlobalTranslation(self, jointName, time=0):
        fbxNode = self.getNode(jointName)
        self.time.Set(time)
        return self.getNode(jointName).EvaluateGlobalTransform(self.time).GetRow(3)

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

    def writeDataFile(self,filePath):
        pass

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
                for frame in range(scene.startTime,scene.endTime):
                    line = []
                    for jointName in nnConfigObj.input.keys():
                        print "fbxGroup: %s fbxScene: %s frame: %s joint: %s" % \
                                    (fbxGroupName,scene.fileName,int(frame),jointName)
                        for transform in nnConfigObj.input[jointName]:
                            if transform == "pos":
                                line = line + list(scene.getGlobalTranslation(jointName,frame))
                            if transform == "rot":
                                line = line + [1,2,3]
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

        



