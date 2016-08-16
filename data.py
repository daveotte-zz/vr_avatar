import sys
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
        self.data = json.loads(open(jsonFilePath).read())
        
        #encapsulate fbxs json data into fbx objects
        self.dataObjects = []
        for d in self.data[dataType]:
            self.dataObjects.append(fbxData(d))
                            
    def getObjByName(self,name): 
        for obj in self.dataObjects:
            if name == obj.name:
                return obj
        return None

    def getObject(self,objectIndexOrName):
        if type(objectIndexOrName) == int:
            return self.getObjByIndex(objectIndexOrName)
        else:
            return self.getObjByName(objectIndexOrName)
            
    def getObjByIndex(self,index): 
        for obj in self.dataObjects:
            if index == obj.index:
                return obj
        return None

class fbxData(object):
    """
    Make object behave like a dictionary.
    """
    def __init__(self, data):
        self.__dict__ = data

class fbxManager(dataManager):
    """
    Initalize class with json file containing data on all available anim fbxs.
    Makes it easy to get anim fbx data, and keep track of current fbx while
    the program runs. Use an instance of this object to initialize timeManger.
    """
    def __init__(self, dataType):
        dataManager.__init__(self, dataType)        
        #set the 'current fbx' as specified in the json config file
        self.setCurrentFbx(self.data['config']['referenceFbx'])
        self.config = self.data['config']
        
    def setCurrentFbx(self,indexOrName):
        self.currentFbx = self.getObject(indexOrName)
        return None

   

class nnManager(object):
    """
    Manage NN construction based on json configuration.
    """
    def __init__(self, fbxManager):
 
        self.fm = fbxManager
        



