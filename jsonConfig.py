import os

#return abs path to a json file. Why do I have to do this?
class jsonFile(object):
    def __init__(self):
        self.filePath =  os.path.dirname(__file__) + '/config/fbx.json'

    def getJsonFile(self):
        return self.filePath