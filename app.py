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
        self.nns = []
        for nnConfig in self.nnConfigs:
            #self.nnTestDataDict[nnConfig] = nnData(nnConfig, fbxTestingScenes)
            nnDataObj = nnData(nnConfig, self.fbxTrainingScenes)
            self.nnTrainDataDict[nnConfig] = nnDataObj
            self.nns.append(NN(nnDataObj))
        

    def run(self,nnConfig):
        #find the right nn
        nn = self.getNnByNnConfig(nnConfig)
        nn.job = Process(target=runNN, args=(nn,))
        nn.job.start()

    def terminate(self,nnConfig):
        #find the right nn
        nn = self.getNnByNnConfig(nnConfig)
        print "========================Terminating: %s========================"%(nn.nnConfig.name)
        nn.job.terminate()


    def getNnByNnConfig(self,nnConfig):
        for nn in self.nns:
            if nnConfig.name == nn.nnConfig.name:
                return nn

def runNN(nn):
    print "========================Training: %s========================"%(nn.nnConfig.name)
    nn.run()
    print "========================Finished training: %s========================"%(nn.nnConfig.name)


'''
def main(args):
    if len(args)==1:
        args.append("-gui")
    app = App()

    if args[1] == "-noGui":
        for nn in app.nns:
            p = Process(target=runNN, args=(nn,))
            p.start()
    else:
        ApplicationUI = UI(app)
'''

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