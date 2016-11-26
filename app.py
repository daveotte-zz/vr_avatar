

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
import threading


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
        self.threadId = 0

    def runAll(self):
        for nnConfig in self.nns.keys():
            nn = self.nns[nnConfig]
            nnThread(self.threadId,nn).start()
            self.threadId = self.threadId + 1
        

    def run(self,nnConfig):
        nn = self.nns[nnConfig]
        nnThread(self.threadId,nn).start()
        self.threadId = self.threadId + 1


class nnThread (threading.Thread):
    def __init__(self, threadId, nn):
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = nn.name
        self.nn = nn
    def run(self):
        print "=======================Starting " + self.name + " ======================================="
        self.nn.run()
        print "=======================Exiting " + self.name + " ======================================="

