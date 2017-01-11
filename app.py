from multiprocessing import Process
from lib.nn import NN
from ui.gui import UI
import sys
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
import time
from threading import Thread


# Application class
class App(object):
    def __init__(self):
        jsonNodes               = json.loads(open(getJsonFile()).read())
        self.fbxTrainingScenes  = fbxManager(jsonNodes['trainingGroupIndices']).fbxScenes
        self.fbxTestingScenes   = fbxManager(jsonNodes['testingGroupIndices']).fbxScenes

        #initializing takes a long time if done one at a time, so:
        '''
        for fbxScene in self.fbxTrainingScenes:
            fbxScene.thread = Thread(target=self.initializeFbxScene, args=(fbxScene,))
            fbxScene.thread.start()
        '''
        self.nnConfigs          = nnConfigDataManager(jsonNodes['nnConfigs']).nnConfigs

        self.nnTestDataDict = {}
        self.nnTrainDataDict = {}
        self.nns = []
        for nnConfig in self.nnConfigs:
            #store nn's as dict (self.nnTest/TrainDataDict), AND a list (self.nns)
            nnDataObj = nnData(nnConfig, self.fbxTrainingScenes)
            self.nnTrainDataDict[nnConfig] = nnDataObj
            self.nns.append(NN(nnDataObj))
        
    def run(self,nnConfig):
        nn = self.getNnByNnConfig(nnConfig)
        nn.run()
        #nn.job = Process(target=runNN, args=(nn,))
        #nn.job.start()

    def terminate(self,nnConfig):
        nn = self.getNnByNnConfig(nnConfig)
        print "========================Terminating: %s========================"%(nn.nnData.nnConfig.name)
        nn.job.terminate()


    def getNnByNnConfig(self,nnConfig):
        for nn in self.nns:
            if nnConfig.name == nn.nnData.nnConfig.name:
                return nn

    def initializeFbxScene(self,fbxScene):
        fbxScene.initialize()

def runNN(nn):
    print "========================Training: %s========================"%(nn.nnData.nnConfig.name)
    nn.run()
    print "========================Finished training: %s========================"%(nn.nnData.nnConfig.name)

if __name__ == "__main__":
    if len(sys.argv)==1:
        sys.argv.append("-gui")
    app = App()
    if sys.argv[1] == "-noGui":
        #train all nn's
        for nn in app.nns:
            nn.job = Process(target=runNN, args=(nn,))
            nn.job.start()
    else:
        ApplicationUI = UI(app)



   #main(sys.argv)