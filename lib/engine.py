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
sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from DisplayGlobalSettings  import *
from DisplayHierarchy       import DisplayHierarchy
from DisplayMarker          import DisplayMarker
from DisplayMesh            import DisplayMesh
from DisplayUserProperties  import DisplayUserProperties
from DisplayPivotsAndLimits import DisplayPivotsAndLimits
from DisplaySkeleton        import DisplaySkeleton
from DisplayNurb            import DisplayNurb
from DisplayPatch           import DisplayPatch
from DisplayCamera          import DisplayCamera
from DisplayLight           import DisplayLight
from DisplayLodGroup        import DisplayLodGroup
from DisplayPose            import DisplayPose
from DisplayAnimation       import DisplayAnimation
from DisplayGenericInfo     import DisplayGenericInfo

from FbxCommon import *
import numpy as np
from keras.models import model_from_json
from keras.models import Sequential
from pprint import pprint

class engine(object):
    """
    Composes nn data using and an nnConfig object and list of scenes.
    """
    def __init__(self,nnConfig,trainingScenes,testingScenes):
        self.nnConfig = nnConfig
        self.name = self.nnConfig.name
        self.trainingScenes = trainingScenes
        self.testingScenes = testingScenes
        self.scenes = self.trainingScenes + self.testingScenes

        self.operation = fbxOperationClass = getattr(op, self.nnConfig.fbxMethod)
        self.fbxOperation = fbxOperationClass()

        viveOperationClass = getattr(op, self.nnConfig.viveMethod)
        self.viveOperation = viveOperationClass()
        
        self.loadModel()

        #initially just make the first scene the current scene. 
        self.scene = self.trainingScenes[0]
        self.frame = 0
        self.data = False

    @property 
    def title(self):
        return util.camel2Title(self.name)

    def setData(self):
        self.data = []
        for transforms in self.extractedTransforms():
            inputLinePortion, outputLinePortion = self.fbxOperation.operate(transforms)
            line = inputLinePortion + outputLinePortion
            self.data.append(line)
        self.inputStart = 0
        self.inputEnd = len(inputLinePortion)
        self.outputStart = self.inputEnd  
        self.outputEnd = self.outputStart + len(outputLinePortion)    
        

    def loadModel(self):
        self.fbxOperation.setModelFiles(self.nnConfig.readNnFile,self.nnConfig.readWeightsFile)
        self.viveOperation.setModelFiles(self.nnConfig.readNnFile,self.nnConfig.readWeightsFile)


    def extractedTransforms(self):
        """
        A list of numpy mx4 lists that will
        be used per the nnConfig object.
        """
        bigTransformList = []
        for scene in self.trainingScenes:
            bigTransformList =  bigTransformList + self.extractedTransformsOverFrameRange(scene,\
                                                                                scene.startTime,\
                                                                                scene.endTime+1)
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
        if self.scene.type == "fbx":
            self.operation = self.fbxOperation
            print "Set to fbx operation."
        else:
            self.operation = self.viveOperation
            print "Set to vive operation"
        transforms = self.extractedTransformsAtFrame()
        self.operation.operate(transforms)

    def drawSkeleton(self,transformScale,drawTransforms=True):
        self.scene.drawSkeleton(self.frame,transformScale,drawTransforms)

    def drawSkeletonRecomposed(self,transformScale,drawTransforms=True):
        print "draw recomposed skeleton at frame: %d"%(self.frame)
        self.updateTransforms()
        self.scene.drawSkeleton(self.frame,transformScale,drawTransforms,self.fbxOperation.skipJoints)

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