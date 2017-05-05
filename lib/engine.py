from multiprocessing import Process

import os
import json
import site
import random
import sys
import re
import util 
import lib.operations as op
from path import Path
from threading import Thread
import ast
from collections import OrderedDict
from FbxCommon import *
import numpy as np
from keras.models import model_from_json
from keras.models import Sequential
from pprint import pprint
import copy

class engine(object):
    """
    Composes nn data using and an nnConfig object and list of scenes.
    """
    def __init__(self,nnConfig,trainingScenes=[],testingScenes=[]):
        

        self.nnConfig = nnConfig
        self.name = self.nnConfig.name
        self.trainingScenes = trainingScenes
        self.testingScenes = testingScenes
        self.scenes = self.trainingScenes + self.testingScenes
        try:
            self.operation = fbxOperationClass = getattr(op, self.nnConfig.fbxMethod)
        except:
            print "operations.py has no '%s' class to process the scenes."% (self.nnConfig.fbxMethod)

        self.operation = fbxOperationClass()
        
        self.loadModel()

        #initially just make the first scene the current scene. 
        try:
            self.scene = self.trainingScenes[0]
        except:
            print sys.exc_info()[0]
            print "There are no training scenes."
        self.frame = 0
        self.data = False
        self.dataMirror = []

    @property 
    def title(self):
        return util.camel2Title(self.name)

    def setData(self):
        self.data = []
        extractedTransforms = self.extractedTransforms()

        #we need to deep copy, since processing will change the list for another use.
        if self.nnConfig.mirror:
            self.processTransforms(extractedTransforms,mirror=True)

        inputLinePortion, outputLinePortion = self.processTransforms(extractedTransforms, mirror=False)
        
        self.inputStart = 0
        self.inputEnd = len(inputLinePortion)
        self.outputStart = self.inputEnd  
        self.outputEnd = self.outputStart + len(outputLinePortion)    

        #does this free memory? It's was a pretty darn big list.
        extractedTransforms = []

    def processTransforms(self,extractedTransforms,mirror=False):
        if mirror:
            print "================================ MIRRORING ==========================================="
        else:
            print "=============================== NO MIRRORING ========================================"
        for sceneTransforms in extractedTransforms:
            #new scene, so clear frame cache
            self.operation.clearCache()
            sceneTransformsCopy = copy.deepcopy(sceneTransforms)
            for transforms in sceneTransformsCopy:
                inputLinePortion, outputLinePortion = self.operation.operate(transforms,mirror)
                line = inputLinePortion + outputLinePortion
                self.data.append(line)
        return inputLinePortion, outputLinePortion        

    def loadModel(self):
        self.operation.setModelFiles(self.nnConfig.readNnFile,self.nnConfig.readWeightsFile)


    def extractedTransforms(self):
        """
        A list of numpy mx4 lists that will
        be used per the nnConfig object.
        The nnConfig objects list the joints we want to extract,
        and then this 'bigTransformList' is a python list of frames.
        Each frame is a list of numpy 4x4 matrices extracted from
        the fbx/vive scenes. This is the raw data, and not formated
        yet...'set Data' processes all this data into a clean numpy
        array that the NN will like.
        """
        bigTransformList = []
        for scene in self.trainingScenes:

            #add 1 to start time to avoid initial t-pose. I'm not sure why I'm adding
            #1 to endTime. I'm sure it's for a great reason.
            bigTransformList.append(self.extractedTransformsOverFrameRange(scene,\
                                                                           scene.startTime+1,\
                                                                           scene.endTime+1))
            scene.destroy()
        
        return bigTransformList

    def extractedTransformsOverFrameRange(self,scene,start,end):
        sceneTransforms = []
        for frame in range(start, end+1):
            sceneTransforms.append(self.extractedTransformsAtFrame(scene,frame))
        return sceneTransforms
    
    def extractedTransformsAtFrame(self,scene=False,frame=False):
        """
        List of numpy mx4 lists. Numpy mx4 list is for each joint specified in nn configuration.
        If scene not specified, scene assigned to self.scene is used (same for frame)
        """
        if not scene:
            scene = self.scene
        transformsAtFrame = []
        if not frame:
            frame = self.frame

        for jointNameAndTransformType in self.nnConfig.transforms:
            #extract transforms we will process
            transformsAtFrame.append(scene.getFbxNodeNpTransformAtFrame \
                                    (jointNameAndTransformType[0],\
                                     frame,\
                                     jointNameAndTransformType[1]))
        return transformsAtFrame

    def updateTransforms(self):
        print "Updating Transforms"
        transforms = self.extractedTransformsAtFrame()
        if self.scene.type == "vive":
            transforms = self.operation.vive2fbx(transforms)
        self.operation.operate(transforms)

    def drawSkeleton(self,transformScale,drawTransforms=True):
        self.scene.drawSkeleton(self.frame,transformScale,drawTransforms)

    def drawSkeletonRecomposed(self,transformScale,drawTransforms=True):
        print "draw recomposed skeleton at frame: %d"%(self.frame)
        self.updateTransforms()
        self.scene.drawSkeleton(self.frame,transformScale,drawTransforms,self.operation.skipJoints)

    def drawExtracted(self,transformScale):
        print "draw extracted at frame: %d"%(self.frame)
        self.updateTransforms()
        self.operation.drawExtracted(transformScale)

    def drawManipulated(self,transformScale):
        print "draw manipulated at frame: %d"%(self.frame)
        self.updateTransforms()
        self.operation.drawManipulated(transformScale)

    def drawPredicted(self,transformScale):
        print "draw predicted at frame: %d"%(self.frame)
        self.updateTransforms()
        self.operation.drawPredicted(transformScale)

    def drawRecomposed(self,transformScale):
        print "draw recomposed at frame: %d"%(self.frame)
        self.updateTransforms()
        self.operation.drawRecomposed(transformScale)

    def write(self):
        writeDir = self.nnConfig.writeCsvFile.dirname()
        if not writeDir.isdir():
            print "Making log dir: %s"%(writeDir)
            writeDir.makedirs()

        dataFile = open(self.nnConfig.writeCsvFile,'w')
        for line in self.data:
            #convert line to string. 
            l = ', '.join(str(ln) for ln in line)
            dataFile.write("%s\n" % l)

    def setScene(self,sceneName):
        for scene in self.scenes:
            if scene.name == sceneName:
                self.scene = scene
                print "Scene set to: %s"%(self.scene.title)
                return
        print "Scene: %s does not exist."%(sceneName)

    def printData(self):
        for l in self.data:
            print l