import numpy as np
import lib.util as util
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import copy
from rig.joints import *
from keras.models import Sequential
from keras.models import model_from_json
import json

class operation(object):
    def __init__(self):
        self.inputArray =  []
        self.outputArray = []

        #transforms stored per n frames
        self.frames = []

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
        self.dataMeanList = []
        self.dataStdevList = []

        self.lineSize = 2
        self.lineColor = [1.0,1.0,1.0]

        self.scaleOffset = 1.0

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
            jsonFile.close()
            jsonFile = open(self.modelJsonFile,'r')
            jsonNodes = json.loads(jsonFile.read())
            self.dataMeanList = jsonNodes['dataMeanList']
            self.dataStdevList = jsonNodes['dataStdevList']

        else:
            model =  False
        self.model = model

    def clearCache(self):
        """
        An instance of this class 'operation' will store self.frames worth
        of input data. When processing of extracted transforms 
        switches to a new scene (animation clip), we need to start over to avoid
        discontinuity over the stored frames. This method gets called
        when operation is used to extract transform on a new scene.
        """
        self.inputArray = []
        print "Cache cleared."

    def vive2fbx(self,transformList):
        hmdMx4 = transformList[0]
        rControllerMx4 = transformList[1]
        lControllerMx4 = transformList[2]

        self.joints = joints('/home/daveotte/work/vr_avatar/rig/avatar.xml')

        #apply head local offset

        #get xml hmd joint, who's parent is the world
        hmdJoint = self.joints.getJoint('hmd')

        #place the xml hmd joint per vive telemetry
        hmdJoint.npMx = hmdMx4

        #get the headMx4, which is the local offset from hmdJoint.
        #now headMx4 is like an fbx headMx4
        headMx4 = self.joints.getJoint('head').GetNodeGlobalTransform()

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)
        #send head to origin (leave behind the pos information...)
        headMx4 = util.extractRot(headMx4)

        #RIGHT
        #apply rHand local offset
        rControllerJoint = self.joints.getJoint('rController')
        rControllerJoint.npMx = rControllerMx4
        rHandMx4 = self.joints.getJoint('rHand').GetNodeGlobalTransform()

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandPosV3 = rHandPosV3 * self.scaleOffset
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #LEFT
        #apply lHand local offset
        lControllerJoint = self.joints.getJoint('lController')
        lControllerJoint.npMx = lControllerMx4
        lHandMx4 = self.joints.getJoint('lHand').GetNodeGlobalTransform()       

        #send lHand to the origin with head offset (and scale...I'm bigger.)
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandPosV3 = lHandPosV3 * self.scaleOffset
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #we brought everything to the origin for easy scaling,
        #so now let's put it back:

        #put head back:
        headPosV3scaled = headPosV3
        headPosV3scaled[1] = self.scaleHeightOffset * headPosV3[1]
        headMx4 = util.setPos(headMx4,headPosV3scaled)

        #put rHand back:
        rHandPosV3 = util.getPosArray(rHandMx4) + headPosV3scaled
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)

        #put lHand back:
        lHandPosV3 = util.getPosArray(lHandMx4) + headPosV3scaled
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #pack it up and return it.
        transformList[0] = headMx4
        transformList[1] = rHandMx4
        transformList[2] = lHandMx4

        return transformList




    def runPrediction(self):
        #that [0] needs to happen, but may not work that way.
        #may need to put in variable first, and var[0]
        if not self.model:
            self.updateModel()

        inputData = util.normalizeData(np.array([self.inputArray]),self.dataMeanList,self.dataStdevList)
        self.updatePredicted(self.model.predict_on_batch(inputData)[0])

    def drawExtracted(self,transformScale):
        print "Drawing Extracted--------------------------"
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
                    + [headPosV3[1]]\
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
        #self.recomposedTransforms = self.recomposedTransforms + transforms[0:3] # leave off forearm


class predictElbowPosRotVive(operation):
    def __init__(self):
        super(predictElbowPosRotVive, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = ['rForeArm','rHand']
        self.scaleOffset = .85
    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],    
        """
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
                        + [self.headPosV3[1]]\
                        + util.getTransformArray(lHandMx4).tolist()
        self.outputArray = util.getPosArray(rForeArmMx4).tolist() + util.getRotArray(rForeArmMx4).tolist()

        #normalize
        #self.inputArray = util.normalizeData(self.inputArray)

        #for draw
        self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4,rForeArmMx4]
        self.manipulatedPositions = [util.getPosArray(rForeArmMx4)]


        self.rForeArmPosV3  = util.getPosArray(rForeArmMx4)

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
        #unscale
        #self.recomposeElbowPos = self.recomposeElbowPos*(1/self.scaleOffset)
        self.recomposeElbowPos = self.recomposeElbowPos*1
        self.recomposedPositions = [self.headPosV3+self.recomposeElbowPos]
        recomposedElbowTransform = copy.copy(self.predictedTransforms[0])
        recomposedElbowTransform = util.setPos(recomposedElbowTransform,self.recomposedPositions[0])
        self.recomposedTransforms = [recomposedElbowTransform]

        transforms = copy.copy(self.manipulatedTransforms)
        for transform in transforms[0:3]:
            pos = util.getPosArray(transform)
            pos = pos * (1/self.scaleOffset)
            util.setPos(transform,pos)
            self.recomposedTransforms.append(util.addPosToMx4(transform,self.headPosV3))
        #self.recomposedTransforms = self.recomposedTransforms + transforms[0:3] # leave off forearm















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




class predictNeckPosRot(operation):
    def __init__(self):
        super(predictNeckPosRot, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = ['neck','rHand']
    
    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["neck", "world"],    
        """
        self.extractedTransforms = copy.deepcopy(transformList)

        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        neckMx4 = transformList[3]

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

        #send neck to the origin with head offset
        neckPosV3 = util.getPosArray(neckMx4)
        neckPosV3 = neckPosV3 - headPosV3
        neckMx4 = util.setPos(neckMx4, neckPosV3)

        self.inputArray  = util.getTransformArray(rHandMx4).tolist() \
                    + util.getRotArray(headMx4).tolist() \
                    + [headPosV3[1]]\
                    + util.getTransformArray(lHandMx4).tolist()

        self.outputArray = util.getPosArray(neckMx4).tolist() + util.getRotArray(neckMx4).tolist()

        #for draw
        self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4,neckMx4]
        self.manipulatedPositions = [util.getPosArray(neckMx4)]

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.neckPosV3 = neckPosV3

        #return as python lists...apparently.
        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' 
        Format results of prediction into positions and transforms.
        These will be drawn.
        '''
        self.predictedPositions = [predictedOutput[0:3]]
        neckTransform = util.setPos(util.identity(),predictedOutput[0:3])

        neckTransform = util.setRot(neckTransform,predictedOutput[3:12])
        neckTransform = util.orthonormalize(neckTransform)
        self.predictedTransforms = [neckTransform]

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposeNeckPos = copy.copy(self.predictedPositions[0])
        self.recomposedPositions = [self.headPosV3+self.recomposeNeckPos]
        recomposedNeckTransform = copy.copy(self.predictedTransforms[0])
        recomposedNeckTransform = util.setPos(recomposedNeckTransform,self.recomposedPositions[0])
        self.recomposedTransforms = [recomposedNeckTransform]

        transforms = copy.copy(self.manipulatedTransforms)
        for transform in transforms[0:3]:
            self.recomposedTransforms.append(util.addPosToMx4(transform,self.headPosV3))
        #sself.recomposedTransforms = self.recomposedTransforms + transforms[0:3] # leave off forearm


























class predictEverything(operation):
    def __init__(self):
        super(predictEverything, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = []
    
    def operate(self,transformList):
        """
                            ["head", "world"],
                            ["rHand", "world"],    
                            ["lHand", "world"],    
                            ["hip", "world"],    
                            ["abdomen", "world"],    
                            ["chest", "world"],    
                            ["neck", "world"],    
                            ["rCollar", "world"],    
                            ["rShldr", "world"],    
                            ["rForeArm", "world"],     
                            ["rButtock", "world"],    
                            ["rThigh", "world"],    
                            ["rShin", "world"],    
                            ["rFoot", "world"],    
                            ["rForeArm", "world"],
                            ["lCollar", "world"],    
                            ["lShldr", "world"],    
                            ["lForeArm", "world"],       
                            ["lButtock", "world"],    
                            ["lThigh", "world"],    
                            ["lShin", "world"],    
                            ["lFoot", "world"],    
                            ["lForeArm", "world"]
        """
        self.extractedTransforms = copy.deepcopy(transformList)


        self.inputArray = []
        for transform in transformList:
            self.inputArray = self.inputArray + util.getTransformArray(transform,exclude4thColumn=True).tolist()

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
        #self.recomposedTransforms = self.recomposedTransforms + transforms[0:3] # leave off forearm




###
# Do the same thing to N joints
class predictNPosRot(operation):
    def __init__(self):
        super(predictNPosRot, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = ['rForeArm','rHand']
        self.timeBuffer = 6
    
        self.scaleOffset = 0.75
        self.scaleHeightOffset = 0.85

        self.curPrevHeadList = [[0.0,0.0,0.0],[0.0,0.0,0.0]]


        self.positionOnly = False

    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],   
                                .... 
        """
        #The number of frames stored to deliver as training input
        self.extractedTransforms = copy.deepcopy(transformList)

        for i in range(len(self.extractedTransforms)):
            self.extractedTransforms[i] = util.flipMx(self.extractedTransforms[i])


        headMx4 = transformList.pop(0)
        rHandMx4 = transformList.pop(0)
        lHandMx4 = transformList.pop(0)

        self.transformCount = len(transformList)

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
        for i in range(len(transformList)):
            V3 = util.getPosArray(transformList[i])
            V3 = V3 - headPosV3
            transformList[i] = util.setPos(transformList[i], V3)

        self.curPrevHeadList.pop(0)
        self.curPrevHeadList.append(headPosV3)
        velocity = self.curPrevHeadList[1]-self.curPrevHeadList[0]

        #length of array divided by one frame's worth of dimensions
        # 12 + 9 + 1 + 12 = 34 per frame 


        if self.positionOnly:
            self.currentInputArray = []
            self.currentInputArray = util.getTransformArray(rHandMx4,True).tolist() \
                            + util.getRotArray(headMx4).tolist() \
                            + [headPosV3[1]]\
                            + velocity.tolist()\
                            + util.getTransformArray(lHandMx4,True).tolist()
        else:
            self.currentInputArray = []
            self.currentInputArray = util.getTransformArray(rHandMx4,True).tolist() \
                            + util.getRotArray(headMx4).tolist() \
                            + [headPosV3[1]]\
                            + velocity.tolist()\
                            + util.getTransformArray(lHandMx4,True).tolist()            

        while len(self.inputArray)/len(self.currentInputArray) < self.timeBuffer:
            print "there's not enough in the buffer."
            self.inputArray = self.inputArray + self.currentInputArray
        
        #lop off the first frame
        del self.inputArray[:len(self.currentInputArray)]

        #push on the current frame
        self.inputArray = self.inputArray + self.currentInputArray
        
        #and the things we are trying to predict
        self.outputArray = []

        if self.positionOnly:
            for transform in transformList:
                self.outputArray = self.outputArray + util.getPosArray(transform).tolist() 
        else:
            for transform in transformList:
                self.outputArray = self.outputArray + util.getPosArray(transform).tolist() + util.getRotArray(transform).tolist()

        #for draw

        if not self.positionOnly:
            self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4] + transformList

        self.manipulatedPositions = []
        for transform in transformList:
            self.manipulatedPositions.append(util.getPosArray(transform))

        self.manipulatedPositions.append(velocity.tolist())

        # stuff for recompose
        self.headPosV3 = headPosV3
        #self.rForeArmPosV3 = rForeArmPosV3

        #return as python lists...apparently.
        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' 
        Format results of prediction into positions and transforms.
        These will be drawn.
        '''

        if self.positionOnly:
            posStart = 0
            posEnd = 3
            offset = 3
            self.predictedTransforms = []
            self.predictedPositions = []
            for i in range(self.transformCount):
                ###
                ### turn the huge output array into prediction transforms

                #pull out position from predicted output array
                self.predictedPositions.append(predictedOutput[posStart:posEnd])

                posStart += offset
                posEnd += offset
        else:

            posStart = 0
            posEnd = 3
            rotEnd = 12
            offset = 12
            self.predictedTransforms = []
            self.predictedPositions = []
            for i in range(self.transformCount):
                print "this is my index: %d"%(i)
                ###
                ### turn the huge output array into prediction transforms

                #pull out position from predicted output array
                self.predictedPositions.append(predictedOutput[posStart:posEnd])

                #manufacture a transform with the position
                transform = util.setPos(util.identity(),predictedOutput[posStart:posEnd])

                #pull out the rotation array, and complete the transform construction
                transform = util.setRot(transform,predictedOutput[posEnd:rotEnd])
                transform = util.orthonormalize(transform)
                self.predictedTransforms.append(transform)
                posStart += offset
                posEnd += offset
                rotEnd += offset

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposedPositions  = []
 
        ### recomposed transforms should end up in same order for drawing later.

        #recomposed the manipulated xforms (not predicted) This is for vive, since we have offset to add.

        self.recomposedTransforms = []

        if not self.positionOnly:
            transforms = copy.copy(self.manipulatedTransforms)
            for transform in transforms[0:3]:
                self.recomposedTransforms.append(util.addPosToMx4(transform,self.headPosV3))


        #now lets recompose the predicted positions and transforms. (mark predictd with magenta dot)
        for pos in self.predictedPositions:
            #get the predicted pos to recompose
            position = copy.copy(pos)
        
            #recompose the position
            self.recomposedPositions.append(self.headPosV3+position)
        
 
        if not self.positionOnly:       
            for i in range(len(self.predictedTransforms)):
                #get the predicted transform
                recomposedTransform = copy.copy(self.predictedTransforms[i])
                
                #keep the rotation, but offset with recomposed position
                self.recomposedTransforms.append(util.setPos(recomposedTransform,self.recomposedPositions[i])) 




    def drawRecomposed(self,transformScale):
        self.runPrediction()
        self.updateRecompose()


        if not self.positionOnly:
            util.drawMxs(self.recomposedTransforms,transformScale)
        util.drawPoints(self.recomposedPositions,9,util.color.magenta)

        '''
        0 ["rHand", "world"],    
        6 ["rForeArm", "world"],     
        5 ["rShldr", "world"],   
        4 ["neck", "world"],        
        1 ["head", "world"], 

        4 ["neck", "world"],        
        7 ["lShldr", "world"],    
        8 ["lForeArm", "world"]  
        2 ["lHand", "world"],    

        3 ["hip", "world"],  
        4 ["neck", "world"],       


        1   ["head", "world"],
        0   ["rHand", "world"],    
        2   ["lHand", "world"],    
        3   ["hip", "world"],  
        4   ["abdomen", "world"],         
        5   ["neck", "world"],       
        6   ["rShldr", "world"],    
        7   ["rForeArm", "world"],     
        8   ["lShldr", "world"],    
        9   ["lForeArm", "world"],    
        10  ["rFoot", "world"],    
        11  ["lFoot", "world"],    
        12  ["rShin", "world"],    
        13  ["lShin", "world"],    
        14  ["rThigh", "world"],    
        15  ["lThigh", "world"] 
----------------------------------------

        0   ["rHand", "world"],    
        7   ["rForeArm", "world"],     
        6   ["rShldr", "world"],    
        5   ["neck", "world"],       
        8   ["lShldr", "world"],    
        9   ["lForeArm", "world"],    
        2   ["lHand", "world"],    

        1   ["head", "world"],
        5   ["neck", "world"],       
        4   ["abdomen", "world"],         
        3   ["hip", "world"],  

        10  ["rFoot", "world"],    
        12  ["rShin", "world"],    
        14  ["rThigh", "world"],    
        3   ["hip", "world"],  
        15  ["lThigh", "world"] 
        13  ["lShin", "world"],    
        11  ["lFoot", "world"],    

        '''  
        util.drawLines([util.getPosArray(self.recomposedTransforms[0]), \
                        util.getPosArray(self.recomposedTransforms[7]), \
                        util.getPosArray(self.recomposedTransforms[6]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[8]), \
                        util.getPosArray(self.recomposedTransforms[9]), \
                        util.getPosArray(self.recomposedTransforms[2])], \
                        self.lineSize,self.lineColor)

        util.drawLines([util.getPosArray(self.recomposedTransforms[1]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[3])], \
                        self.lineSize,self.lineColor)

        util.drawLines([util.getPosArray(self.recomposedTransforms[10]), \
                        util.getPosArray(self.recomposedTransforms[12]), \
                        util.getPosArray(self.recomposedTransforms[14]), \
                        util.getPosArray(self.recomposedTransforms[3]), \
                        util.getPosArray(self.recomposedTransforms[15]), \
                        util.getPosArray(self.recomposedTransforms[13]), \
                        util.getPosArray(self.recomposedTransforms[11])], \
                        self.lineSize,self.lineColor)


'''

        util.drawLines([util.getPosArray(self.recomposedTransforms[0]), \
                        util.getPosArray(self.recomposedTransforms[6]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[1])], \
                        self.lineSize,self.lineColor)
        util.drawLines([util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[7]), \
                        util.getPosArray(self.recomposedTransforms[8]), \
                        util.getPosArray(self.recomposedTransforms[2])], \
                        self.lineSize,self.lineColor)


        util.drawLines([util.getPosArray(self.recomposedTransforms[3]), \
                        util.getPosArray(self.recomposedTransforms[4])], \
                        self.lineSize,self.lineColor)

'''



