

import sys
from lib.data import *
from lib.nn import *
from keras.models import Sequential
from keras.models import model_from_json
from keras.layers import Dense
import keras.optimizers
import numpy
from keras.layers.normalization import BatchNormalization
from ui import gui
from PyQt4 import QtGui
import os
import random
import json


# Application class
class App(object):
    def __init__(self):
        jsonNodes               = json.loads(open(getJsonFile()).read())
        self.fbxTrainingScenes  = fbxManager(jsonNodes['trainingGroupIndices']).fbxScenes
        self.fbxTestingScenes   = fbxManager(jsonNodes['testingGroupIndices']).fbxScenes

        self.nnConfigs          = nnConfigDataManager(jsonNodes['nnConfigs']).nnConfigs

        self.nnTestDataDict = {}
        self.nnTrainDataDict = {}
        self.nns = {}
        for nnConfig in self.nnConfigs:
            #self.nnTestDataDict[nnConfig] = nnData(nnConfig, fbxTestingScenes)
            nnDataObj = nnData(nnConfig, self.fbxTrainingScenes)
            self.nnTrainDataDict[nnConfig] = nnDataObj
            self.nns[nnConfig] = NN(nnDataObj)

    def runAll(self):
        for nnConfig in self.nns.keys():
            self.nns[nnConfig].run()
        

    def run(self,nnConfig):
        self.nns[nnConfig].run()





