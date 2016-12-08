

import sys
#from data import datamanafbxManager, nnConfigDataManager, nnData, transformsFilesManager
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
    def __init__(self,nnData):
        self.nnData = nnData
        self.name = self.nnData.nnConfig.name

    def run(self):
        self.nnData.write()
        print "inputStart: %d, inputEnd: %d, outputStart: %d, outputEnd: %d" % \
                                    (self.nnData.inputStart,
                                     self.nnData.inputEnd,  
                                     self.nnData.outputStart,
                                     self.nnData.outputEnd)
        
        inputData, outputData = self.data()
        model = self.model()
        model.fit(inputData,outputData, nb_epoch=self.nnData.nnConfig.epochs, batch_size=1)
        self.write(model)

    def write(self,model):
        writeDir = self.nnData.nnConfig.writeWeightsFile.dirname()
        if not writeDir.isdir():
            print "Making log dir: %s"%(writeDir)
            writeDir.makedirs()

        print "Writing: %s"%(self.nnData.nnConfig.writeWeightsFile)
        model.save_weights(self.nnData.nnConfig.writeWeightsFile)


 
        print "Writing: %s"%(self.nnData.nnConfig.writeNnFile)
        jsonFile = open(self.nnData.nnConfig.writeNnFile,'w')
        jsonFile.write(model.to_json())
        jsonFile.close()

        print "Copying config: %s"%self.nnData.nnConfig.configFile
        copyfile(self.nnData.nnConfig.configFile, self.nnData.nnConfig.writeConfigFile)

        print "Copying operations.py: %s"%self.nnData.nnConfig.operationsFile
        copyfile(self.nnData.nnConfig.operationsFile, self.nnData.nnConfig.writeOperationsFile)

        print "Ticking up the write/read paths."
        self.nnData.nnConfig.setUpLoadPaths()
        print "Reloading NN models."
        self.nnData.loadModel()


    def data(self):
        seed = 7
        np.random.seed(seed)
        dataSet = np.array(self.nnData.data)
        random.shuffle(dataSet)

        inputData = dataSet[:,self.nnData.inputStart:self.nnData.inputEnd]
        outputData = dataSet[:,self.nnData.outputStart:self.nnData.outputEnd]
        
        return inputData, outputData       

    def model(self):
        model = Sequential()

        inputDim = self.nnData.inputEnd
        outputDim = (self.nnData.outputEnd-self.nnData.outputStart)
        
        model.add(Dense(inputDim, input_dim=inputDim, init='normal', activation='relu'))
        model.add(Dense(inputDim*50, init='normal', activation='relu'))
        model.add(Dense(outputDim, init='normal', activation='linear'))

        optim=keras.optimizers.Adagrad(lr=0.01, epsilon=1e-08)
        #optim = keras.optimizers.SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(optimizer=optim, loss='mean_squared_error')

        return model


def predict(model,inputData):
    return model.predict_on_batch(inputData)
