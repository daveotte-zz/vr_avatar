
from lib.scene import *
from pathlib import Path
from FbxCommon import *
import lib.util as util
class dataManager:
    """
    Base class. Converts json nodes to python objects with json node attrs as properties.
    Methods added to access/manipulate the json data.
    'dataType' corresponds to json node name, AND object class type.
    """
    def __init__(self, dataType):
        self.dataType = dataType
        print ("Getting Data type: %s"%dataType)
        self.dataObjects = self.getObjects(json.loads(open(util.getJsonFile()).read()))      
        
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

class sceneManager(dataManager):
    """
    Manages Scene data stored on disk in organized directories (as fbx files or vive .csv telemetry).
    """
    def __init__(self, groupIndices, dataType="sceneGroup"):
        dataManager.__init__(self, dataType) 
        self.groupIndices = groupIndices
        
    def destroy(self):
        for obj in self.dataObjects:
            obj.destroy()

    @property 
    def scenes(self):
        return self.scenesByGroupIndices(self.groupIndices)

    def scenesByGroupIndices(self,groupIndices):
        print (str(groupIndices) + "==========================")
        fbxSceneObjects = []
        for g in self.sceneGroupObjectsByIndices(groupIndices):
            fbxSceneObjects = fbxSceneObjects + g.scenesInGroup()
        return fbxSceneObjects

    def sceneGroupObjectsByIndices(self,groupIndices):
        """
        Return all the fbx data Groups objects that will be
        used per the nnConfig object.
        """
        sceneGroupObjects = []
        for sceneGroupIndex in groupIndices:
            print ('Getting sceneGroup: %s '%(sceneGroupIndex))
            sceneGroupObjects.append(self.getObject(sceneGroupIndex))
        return sceneGroupObjects

class baseData:
    def __init__(self, jsonNode):
        self.__dict__ = jsonNode

    @property 
    def title(self):
        return util.camel2Title(self.name)

class sceneGroup(baseData):
    """
    Append specific methods to deal with fbx data.
    """
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode)

    def destroy(self):
        for scene in self.scenes:
            scene.destroy()

    def sceneFilesInGroup(self):
        files = []
        if hasattr(self, 'dir'):
            for f in os.listdir(self.dir):
                #could be an fbx Scene, or my made up format of vive telemetry).
                if f.endswith('.fbx') or f.endswith('.csv'):
                    files.append(self.dir+'/'+f)
        return files

    def sceneFileNamesInGroup(self):
        names = []
        for file in self.sceneFilesInGroup()():
            names.append(Path(file).stem)
        return names

    def scenesInGroup(self):
        scenesInGroup = []
        for f in self.sceneFilesInGroup():
            print (f)
            sceneClass = self.sceneClass(f)
            scenesInGroup.append(sceneClass(f))
        return scenesInGroup

    def sceneClass(self,file):
        '''
        From the file extension, determine Scene class to create.
        '''
        if file.endswith(".fbx"):
            sceneClass = eval("fbxScene")
        elif file.endswith(".csv"):
            print ("Found csv =====================================================")
            sceneClass = eval("viveScene")

        return sceneClass


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

        self.weightsFileBaseName = self.name+".h5"
        self.nnFileBaseName = self.name+".json"
        
        #dave- check for file, not just directory
        self.checkDir(pathBase,0)

        self.writeWeightsFile = self.writeDir+"/"+self.weightsFileBaseName
        self.writeNnFile = self.writeDir+"/"+self.nnFileBaseName
        self.readWeightsFile = self.readDir+"/"+self.weightsFileBaseName
        self.readNnFile = self.readDir+"/"+self.nnFileBaseName

        self.configFile = "/home/daveotte/work/vr_avatar/lib/config.json"
        self.writeConfigFile = self.writeDir+"/config.json"

        self.operationsFile = "/home/daveotte/work/vr_avatar/lib/operations.py"
        self.writeOperationsFile = self.writeDir+"/operations.py"


        self.writeLogFile = self.writeDir+"/"+self.name+"_log.txt"
        self.writeCsvFile = self.writeDir+"/"+self.name+"_output.csv"

        print ("Setting write file: %s"%(self.writeWeightsFile))
        print ("Setting read file: %s"%(self.readWeightsFile))
        
    def checkDir(self,pathBase,i):
        suffix = '%03d'%i
        logDir = Path(pathBase+str(suffix))
        nextId = i+1
        prevId = i-1
        print ("Checking isdir: " + str(logDir.abspath()))
        if os.path.isdir(str(logDir.abspath())):
            self.checkDir(pathBase,nextId)
        else:
            self.writeDir = logDir
            suffix = '%03d'%prevId  
            self.readDir = Path(pathBase+str(suffix))
            #if this is dir 0 (the first trial ever), then we share the same read/write dir
            if not self.readDir.isdir():   
                self.readDir = self.writeDir




