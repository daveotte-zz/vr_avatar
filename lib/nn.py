

import sys
#from data import datamanafbxManager, nnConfigDataManager, engine, transformsFilesManager
from keras.models import Sequential
from keras.models import model_from_json
from keras.layers import Dense
import keras.optimizers
import numpy as np
from keras.layers.normalization import BatchNormalization
from ui import gui
from PyQt4 import QtGui
import os
from path import Path
import random
from shutil import copyfile


class NN(object):
    def __init__(self,engine):
        self.engine = engine
        self.name = self.engine.name

    def run(self):
        #self.engine.write()
        if not self.engine.data:
            self.engine.setData()
        print "inputStart: %d, inputEnd: %d, outputStart: %d, outputEnd: %d" % \
                                    (self.engine.inputStart,
                                     self.engine.inputEnd,  
                                     self.engine.outputStart,
                                     self.engine.outputEnd)
        
        inputData, outputData = self.data()
        model = self.model()
        model.fit(inputData,outputData, nb_epoch=self.engine.nnConfig.epochs, batch_size=50)
        self.write(model)

    def write(self,model):
        writeDir = self.engine.nnConfig.writeWeightsFile.dirname()
        if not writeDir.isdir():
            print "Making log dir: %s"%(writeDir)
            writeDir.makedirs()

        print "Writing: %s"%(self.engine.nnConfig.writeWeightsFile)
        model.save_weights(self.engine.nnConfig.writeWeightsFile)
 
        print "Writing: %s"%(self.engine.nnConfig.writeNnFile)
        jsonFile = open(self.engine.nnConfig.writeNnFile,'w')
        jsonFile.write(model.to_json())
        jsonFile.close()

        print "Copying config: %s"%self.engine.nnConfig.configFile
        copyfile(self.engine.nnConfig.configFile, self.engine.nnConfig.writeConfigFile)

        print "Copying operations.py: %s"%self.engine.nnConfig.operationsFile
        copyfile(self.engine.nnConfig.operationsFile, self.engine.nnConfig.writeOperationsFile)

        print "Ticking up the write/read paths."
        self.engine.nnConfig.setUpLoadPaths()
        print "Reloading NN models."
        self.engine.loadModel()

    def data(self):
        seed = 7
        np.random.seed(seed)
        dataSet = np.array(self.engine.data)
        random.shuffle(dataSet)

        inputData = dataSet[:,self.engine.inputStart:self.engine.inputEnd]
        outputData = dataSet[:,self.engine.outputStart:self.engine.outputEnd]
        
        return inputData, outputData       

    def model(self):
        model = Sequential()

        inputDim = self.engine.inputEnd
        outputDim = (self.engine.outputEnd-self.engine.outputStart)


        
        model.add(Dense(inputDim, input_dim=inputDim, init='normal', activation='relu'))
        model.add(Dense(150, init='normal', activation='relu'))
        model.add(Dense(outputDim, init='normal', activation='linear'))

        optim=keras.optimizers.Adagrad(lr=0.01, epsilon=1e-08)
        #optim = keras.optimizers.SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(optimizer=optim, loss='mean_squared_error')

        return model



