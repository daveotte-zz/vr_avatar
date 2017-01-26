import numpy as np
import lib.util as util
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import copy
from rig.joints import *
from keras.models import Sequential
from keras.models import model_from_json

class operation(object):
    def __init__(self):
        self.inputArray =  []
        self.outputArray = []

        self.extractedTransforms = []
        self.extractedPositions  = []

        self.manipulatedTransforms = []
        self.manipulatedPositions  = []

        self.predictedTransforms = []
        self.predictedPositions  = []

        self.recomposedTransforms = []
        self.recomposedPositions  = []

        self.skipJoints = []

        self.modelJsonFile = ""
        self.modelWeightsFile = ""
        self.model = False

    def setModelFiles(self,modelJsonFile,modelWeightsFile):
        self.modelJsonFile = modelJsonFile
        self.modelWeightsFile = modelWeightsFile               

    def updateModel(self):
        if self.modelJsonFile.isfile() and self.modelWeightsFile.isfile():
            print "Loading model: %s and %s"%(self.modelJsonFile, self.modelWeightsFile)
            jsonFile = open(self.modelJsonFile,'r')
            jsonString = jsonFile.read().replace('\n', '')
            model = model_from_json(jsonString)
            model.load_weights(self.modelWeightsFile)
        else:
            model =  False
        self.model = model

    def runPrediction(self):
        #that [0] needs to happen, but may not work that way.
        #may need to putin variable first, and var[0]
        if not self.model:
            self.updateModel()
        self.updatePredicted(self.model.predict_on_batch(np.array([self.inputArray]))[0])

    def drawExtracted(self,transformScale):
        util.drawMxs(self.extractedTransforms,transformScale)
        util.drawPoints(self.extractedPositions,9,util.color.magenta)

    def drawManipulated(self,transformScale):
        util.drawMxs(self.manipulatedTransforms,transformScale)
        util.drawPoints(self.manipulatedPositions,9,util.color.magenta)

    def drawPredicted(self,transformScale):
        self.runPrediction()  
        util.drawMxs(self.predictedTransforms,transformScale)  
        util.drawPoints(self.predictedPositions,9,util.color.magenta)

    def drawRecomposed(self,transformScale):
        self.runPrediction()
        self.updateRecompose()
        util.drawMxs(self.recomposedTransforms,transformScale)
        util.drawPoints(self.recomposedPositions,9,util.color.magenta)


class predictElbowPosRot(operation):
    def __init__(self):
        super(predictElbowPosRot, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = ['rForeArm','rHand']
    
    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],    
        """
        self.extractedTransforms = copy.deepcopy(transformList)

        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)

        #send head to origin
        headMx4 = util.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #send rForeArm to the origin with head offset
        rForeArmPosV3 = util.getPosArray(rForeArmMx4)
        rForeArmPosV3 = rForeArmPosV3 - headPosV3
        rForeArmMx4 = util.setPos(rForeArmMx4, rForeArmPosV3)

        self.inputArray  = util.getTransformArray(rHandMx4).tolist() \
                    + util.getRotArray(headMx4).tolist() \
                    + util.getTransformArray(lHandMx4).tolist()

        self.outputArray = util.getPosArray(rForeArmMx4).tolist() + util.getRotArray(rForeArmMx4).tolist()

        #for draw
        self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4,rForeArmMx4]
        self.manipulatedPositions = [util.getPosArray(rForeArmMx4)]

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.rForeArmPosV3 = rForeArmPosV3

        #return as python lists...apparently.
        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' 
        Format results of prediction into positions and transforms.
        These will be drawn.
        '''
        self.predictedPositions = [predictedOutput[0:3]]
        elbowTransform = util.setPos(util.identity(),predictedOutput[0:3])

        elbowTransform = util.setRot(elbowTransform,predictedOutput[3:12])
        elbowTransform = util.orthonormalize(elbowTransform)
        self.predictedTransforms = [elbowTransform]

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposeElbowPos = copy.copy(self.predictedPositions[0])
        self.recomposedPositions = [self.headPosV3+self.recomposeElbowPos]
        recomposedElbowTransform = copy.copy(self.predictedTransforms[0])
        recomposedElbowTransform = util.setPos(recomposedElbowTransform,self.recomposedPositions[0])
        self.recomposedTransforms = [recomposedElbowTransform]

        transforms = copy.copy(self.manipulatedTransforms)
        for transform in transforms[0:3]:
            self.recomposedTransforms.append(util.addPosToMx4(transform,self.headPosV3))
        #sself.recomposedTransforms = self.recomposedTransforms + transforms[0:3] # leave off forearm
































class predictElbowPosVive(operation):
    '''
    Extracted transforms come in, get worked on, and then these things get set:
        1. Formatted input array / self.inputArray
        2. Formatted example output array / self.outputArray
        3. Update manipulated transforms and points to draw / self.manipulatedTransforms/Points
    '''
    def __init__(self):
        super(predictElbowPosVive, self).__init__()
        self.scaleOffset = .85

    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],    
        """

        ####for draw
        self.extractedTransforms = copy.deepcopy(transformList)


        hmdMx4 = transformList[0]
        rControllerMx4 = transformList[1]
        lControllerMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        self.joints = joints('/home/daveotte/work/vr_avatar/rig/avatar.xml')

        #apply rHand local offset
        hmdJoint = self.joints.getJoint('hmd')
        hmdJoint.npMx = hmdMx4
        headMx4 = self.joints.getJoint('head').GetNodeGlobalTransform()

        #get head position v3
        self.headPosV3 = util.getPosArray(headMx4)
        #send head to origin
        headMx4 = util.extractRot(headMx4)

        #RIGHT
        #apply rHand local offset
        rControllerJoint = self.joints.getJoint('rController')
        rControllerJoint.npMx = rControllerMx4
        rHandMx4 = self.joints.getJoint('rHand').GetNodeGlobalTransform()

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - self.headPosV3
        rHandPosV3 = rHandPosV3 * self.scaleOffset
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #LEFT
        #apply lHand local offset
        lControllerJoint = self.joints.getJoint('lController')
        lControllerJoint.npMx = lControllerMx4
        lHandMx4 = self.joints.getJoint('lHand').GetNodeGlobalTransform()

        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - self.headPosV3
        lHandPosV3 = lHandPosV3 * self.scaleOffset
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        self.inputArray = util.getTransformArray(rHandMx4).tolist() \
                        + util.getRotArray(headMx4).tolist() \
                        + util.getTransformArray(lHandMx4).tolist()
        self.outputArray = util.getPosArray(rForeArmMx4).tolist()

        #for draw
        self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4]
        self.manipulatedPositions = [self.outputArray]

        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' Format results of prediction into positions and transforms.
            These will be drawn.
        '''
        self.predictedPositions = [predictedOutput]
        self.predictedTransforms = []

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposedTransforms=[]
        self.recomposeElbowPos = self.predictedPositions[0]
        #unscale
        self.recomposeElbowPos = self.recomposeElbowPos*(1/self.scaleOffset)
        self.recomposedPositions = [self.headPosV3+self.recomposeElbowPos]
        transforms = copy.copy(self.manipulatedTransforms)
        for mx in transforms:
            pos = util.getPosArray(mx)
            pos = pos * (1/self.scaleOffset)
            pos = pos + self.headPosV3
            self.recomposedTransforms.append(util.setPos(mx, pos))

class predictElbowPos(operation):
    def __init__(self):
        super(predictElbowPos, self).__init__()
        self.skipJoints = ['rForeArm','rHand']
    
    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],    
        """
        self.extractedTransforms = copy.deepcopy(transformList)

        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)

        #send head to origin
        headMx4 = util.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #send rForeArm to the origin with head offset
        rForeArmPosV3 = util.getPosArray(rForeArmMx4)
        rForeArmPosV3 = rForeArmPosV3 - headPosV3
        rForeArmMx4 = util.setPos(rForeArmMx4, rForeArmPosV3)

        self.inputArray  = util.getTransformArray(rHandMx4).tolist() \
                    + util.getRotArray(headMx4).tolist() \
                    + util.getTransformArray(lHandMx4).tolist()

        self.outputArray = util.getPosArray(rForeArmMx4).tolist()      

        #for draw
        self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4]
        self.manipulatedPositions = [self.outputArray]

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.rForeArmPosV3 = rForeArmPosV3

        #return as python lists...apparently.
        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' 
        Format results of prediction into positions and transforms.
        These will be drawn.
        '''
        self.predictedPositions = [predictedOutput]
        self.predictedTransforms = []

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposedTransforms=[]
        self.recomposeElbowPos = self.predictedPositions[0]
        self.recomposedPositions = [self.headPosV3+self.recomposeElbowPos]
        transforms = copy.copy(self.manipulatedTransforms)
        for mx in transforms:
            pos = util.getPosArray(mx)
            pos = pos + self.headPosV3
            self.recomposedTransforms.append(util.setPos(mx, pos))
