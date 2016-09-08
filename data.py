import sys
import os
import json
from jsonConfig import jsonFile

"""
Library to work with fbx data.
"""


class dataManager(object):
    """
    Generic class used in different types of 'data managers'.
    """
    def __init__(self, dataType):
        #use jsonConfig module hack to get json config file
        jsonFileObj = jsonFile()
        jsonFilePath = jsonFileObj.getJsonFile()
        self.jsonNodes = json.loads(open(jsonFilePath).read())

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
    
    def __init__(self, dataType):
        dataManager.__init__(self, dataType) 

        #encapsulate fbxs json data into fbx objects
        self.dataObjects = self.getObjects(self.jsonNodes[dataType])

    def getObjects(self, jsonNodes):
        dataObjects = []
        for d in jsonNodes:
            dataObj = fbxData(d)
            if dataObj.name == "config":
                self.config = dataObj
            else:
                dataObjects.append(dataObj)   
        return dataObjects   

class baseData (object):
    def __init__(self, jsonNode):
        self.__dict__ = jsonNode


class fbxData(baseData):
    """
    Make object behave like a dictionary.
    """
    def __init__(self, jsonNode):
        baseData.__init__(self, jsonNode)
        self.fbxFiles = self.getFbxFiles()

    def getFbxFiles(self):
        files = []
        if hasattr(self, 'dir'):
            for f in os.listdir(self.dir):
                if f.endswith('.fbx'):
                    files.append(self.dir+'/'+f)
        return files


        



