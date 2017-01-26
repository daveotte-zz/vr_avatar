from multiprocessing import Process
from lib.nn import NN
from ui.gui import UI
import sys
import sys
from lib.data import *
from lib.engine import *
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
        jsonNodes               = json.loads(open(util.getJsonFile()).read())
        self.trainingScenes  = sceneManager(jsonNodes['trainingGroupIndices']).scenes
        self.testingScenes   = sceneManager(jsonNodes['testingGroupIndices']).scenes

        self.engines = []
        for nnConfig in nnConfigDataManager(jsonNodes['nnConfigs']).nnConfigs:
            self.engines.append(engine(nnConfig, self.trainingScenes, self.testingScenes))

        #initially just make the first engine the current engine.
        self.engine = self.engines[0]
        
    def run(self):
        self.nn = NN(self.engine)
        #nn.run()
        self.nn.job = Process(target=runNN, args=(self.nn,))
        self.nn.job.start()

    def terminate(self):
        print "========================Terminating: %s========================"%(self.nn.name)
        self.nn.job.terminate()

    def initializeScene(self,scene): 
        scene.initialize()

    def setEngine(self,engineName):
        for engine in self.engines:
            if engine.name == engineName:
                self.engine = engine
                self.engine.loadModel()
                return
        print "Engine: %s does not exist."%(engineName)

def runNN(nn):
    print "========================Training: %s========================"%(nn.name)
    nn.run()
    print "========================Finished training: %s========================"%(nn.name)

if __name__ == "__main__":
    if len(sys.argv)==1:
        sys.argv.append("-gui")
    app = App()
    if sys.argv[1] == "-noGui":
        #train all nn's
        for engine in app.engines:
            nn= NN(engine)
            nn.job = Process(target=runNN, args=(nn,))
            nn.job.start()
    else:
        ApplicationUI = UI(app)
