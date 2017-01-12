import numpy as np
import util
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import copy
from rig.joints import *


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

    def runPrediction(self):
        #that [0] needs to happen, but may not work that way.
        #may need to putin variable first, and var[0]
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



class predictElbowVive(operation):
    '''
    Extracted transforms come in, get worked on, and then these things get set:
        1. Formatted input array / self.inputArray
        2. Formatted example output array / self.outputArray
        3. Update manipulated transforms and points to draw / self.manipulatedTransforms/Points
    '''
    def __init__(self):
        super(predictElbowVive, self).__init__()
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


        

class predictElbow(operation):
    def __init__(self):
        super(predictElbow, self).__init__()
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







'''





class predictEverything(object):
    def __init__(self):
        self.transformScale = 1.0
    
    def operate(self,transformList):
        """
                            ["head", "world"],
                            ["rHand", "world"],    
                            ["lHand", "world"],    
                            ["hip", "world"],    
                            ["abdomen", "world"],    
                            ["chest", "world"],    
                            ["neck", "world"],    
                            ["leftEye", "world"],    
                            ["rightEye", "world"],    
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
        posList = []
        for i in range(3,len(transformList)):
            #convert list of transforms to list of positions
            pos = util.getPosArray(transformList[i])
            pos = pos - headPosV3
            posList.append(pos)

        outputArray = []
        #convert numpy 38,3 list to flat python list
        for p in posList:
            outputArray = outputArray + p.tolist()

        #convert back to flat numpy array
        #outputArray = np.array(posList).flatten()

        inputArray = util.getTransformArray(rHandMx4).tolist() + util.getRotArray(headMx4).tolist() + util.getTransformArray(lHandMx4).tolist()


        self.drawMxs = [rHandMx4,headMx4,lHandMx4]
        self.drawPositions = posList

        # stuff for recompose
        self.headPosV3 = headPosV3

        #return as python lists
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put rForeArm as offset from extracted head,
        #instead of as offset from head at origin
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(self.headPosV3 + pos)
            pos = []



    def predict(self,predictedOutputArray):
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(pos)
            pos = []

    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            util.drawMx(mx,self.transformScale)
        for pos in self.drawPositions:
            util.drawPos(pos)








      


class predictShldr(object):
    def __init__(self):
        self.transformScale = 1.0

    def operate(self,transformList):
        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rShldrMx4 = transformList[3]

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

        #send rShldr to the origin with head offset
        rShldrPosV3 = util.getPosArray(rShldrMx4)
        rShldrPosV3 = rShldrPosV3 - headPosV3
        rShldrMx4 = util.setPos(rShldrMx4, rShldrPosV3)

        inputArray = util.getTransformArray(rHandMx4).tolist() + util.getRotArray(headMx4).tolist() + util.getTransformArray(lHandMx4).tolist()

        outputArray = util.getPosArray(rShldrMx4).tolist()      

        self.drawMxs = [rHandMx4,headMx4,lHandMx4,rShldrMx4]
        self.drawPos = outputArray

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.rShldrPosV3 = rShldrPosV3
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put rShldr as offset from extracted head,
        #instead of as offset from head at origin
        self.drawRecomposePos = self.headPosV3 + predictedOutputArray

    def predict(self,predictedOutputArray):
        self.drawRecomposePos = predictedOutputArray

    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        util.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        util.drawPos(self.drawRecomposePos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            util.drawMx(mx,self.transformScale)
        util.drawPos(self.drawPos)






def posFromRot (transformList):
    """
    transformList[0]: extract rotation
    transformList[1]: apply to extracted rotation.
    """

    #process the xforms
    mxA = util.extractRot(transformList[0])
    mxB = util.extractPos(transformList[1])
    mxC = util.multiply(mxA,mxB)

    #rotation of mxA
    inputArray = util.getRotArray(mxA)
    outputArray = util.getPosArray(mxC)

    #return the data as lists
    return inputArray.tolist(), outputArray.tolist()


class predictHip(object):
    def __init__(self):
        self.transformScale = 1.0

    def operate(self,transformList):
        """
        ["head", "world"],
        ["rHand", "world"],    
        ["lHand", "world"],    
        ["hip", "world"] 
        """
        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        hipMx4 = transformList[3]

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

        #send hip to the origin with head offset
        hipPosV3 = util.getPosArray(hipMx4)
        hipPosV3 = hipPosV3 - headPosV3
        hipMx4 = util.setPos(hipMx4, hipPosV3)

        inputArray = util.getTransformArray(rHandMx4).tolist() + util.getRotArray(headMx4).tolist() + util.getTransformArray(lHandMx4).tolist()

        outputArray = util.getTransformArray(hipMx4).tolist()      

        self.drawMxs = [rHandMx4,headMx4,lHandMx4,hipMx4]
        #draw output hip position
        self.drawPos = util.getPosArray(hipMx4).tolist()

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.hipPosV3 = hipPosV3
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put hip as offset from extracted head,
        #instead of as offset from head at origin
        predictedMx =  util.listToNumpyMx(predictedOutputArray)
        self.drawRecomposePos = self.headPosV3 + util.getPosArray(predictedMx)
        self.drawRecomposeMx = util.setPos(predictedMx, self.drawRecomposePos)

    def predict(self,predictedOutputArray): 
        predictedMx =  util.listToNumpyMx(predictedOutputArray)
        self.drawRecomposeMx = predictedMx                  
        self.drawRecomposePos = util.getPosArray(self.drawRecomposeMx) 


    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        util.drawMx(self.drawRecomposeMx,self.transformScale)
        util.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        util.drawMx(self.drawRecomposeMx)
        util.drawPos(self.drawRecomposePos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            util.drawMx(mx,self.transformScale)
        util.drawPos(self.drawPos)



class predictElbowsVel(object):
    def __init__(self):
        self.transformScale = 1.0
        self.prevTransformList = []
        self.predictionOutputArray = []
        
    
    def operate(self,transformList):
        """
                            ["head", "world"],
                            ["rHand", "world"],    
                            ["lHand", "world"],    
                            ["rForeArm", "world"]   
        """
        #store transformlist for the next frame.
        self.prevTransformList.append(copy.copy(transformList))
        if len(self.prevTransformList)>2:
            del self.prevTransformList[0]


        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        headMx4_1 = self.prevTransformList[0][0]
        rHandMx4_1 = self.prevTransformList[0][1]
        lHandMx4_1 = self.prevTransformList[0][2]
        rForeArmMx4_1 = self.prevTransformList[0][3]     

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)

        headPos_1 = util.getPosArray(headMx4_1) - headPosV3
        rHandPos_1 = util.getPosArray(rHandMx4_1) - headPosV3
        lHandPos_1 = util.getPosArray(lHandMx4_1) - headPosV3



        #rForeArmPos_1 = util.getPosArray(rForeArmMx4_1) - headPosV3

        #send head to origin
        headMx4Origin = copy.copy(headMx4)
        headMx4Origin = util.extractRot(headMx4Origin)

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3

        rHandMx4Origin = copy.copy(rHandMx4)
        rHandMx4Origin = util.setPos(rHandMx4Origin, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4Origin = copy.copy(lHandMx4)
        lHandMx4Origin = util.setPos(lHandMx4Origin, lHandPosV3)

        #send rForeArm to the origin with head offset (we just work with pos)
        rForeArmPosV3 = util.getPosArray(copy.copy(rForeArmMx4))
        rForeArmPosV3 = rForeArmPosV3 - headPosV3

        outputArray = rForeArmPosV3.tolist()
        #print "the output array%s"%(str(outputArray))

        #outputArray = np.array(posList).flatten()

        inputArray = util.getTransformArray(rHandMx4Origin,True).tolist() + util.getRotArray(headMx4Origin).tolist() + util.getTransformArray(lHandMx4Origin,True).tolist()
        #inputArray = inputArray + headPos_1.tolist() + rHandPos_1.tolist() + lHandPos_1.tolist() + rForeArmPos_1.tolist()
        inputArray = inputArray + headPos_1.tolist() + rHandPos_1.tolist() + lHandPos_1.tolist() 

        self.drawMxs = [rHandMx4Origin,headMx4Origin,lHandMx4Origin]

        posList = []
        posList.append(rHandPos_1)
        posList.append(headPos_1)
        posList.append(lHandPos_1)
        posList.append(rForeArmPosV3)
        #posList.append(rForeArmPos_1)

        self.drawPositions = posList

        # stuff for recompose
        self.headPosV3 = headPosV3

        self.correct = util.getPosArray(copy.copy(rForeArmMx4))

        #return as python lists
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put rForeArm as offset from extracted head,
        #instead of as offset from head at origin
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(self.headPosV3 + pos)
            pos = []

    def predict(self,predictedOutputArray):
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(pos)
            pos = []


    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)
            #print "predicted %s and correct %s"%(str(pos),str(self.correct))
            util.drawLine(pos,self.correct,1,[1.0,0.0,0.0])
        pointA = np.array([pos[0],pos[1],pos[2]])
        pointB = np.array([self.correct[0],self.correct[1],self.correct[2]])

        errorV3 = pointB-pointA
        errorLength = np.linalg.norm(errorV3)
        
        #print "Writing: %s"%(str(errorLength))
        #logFile = open('/home/daveotte/predictElbowVelError.txt','a')
        #logFile.write(str(round(errorLength,3))+'\n')
        #logFile.close()

    def draw(self):
        for mx in self.drawMxs:
            util.drawMx(mx,self.transformScale)
        for pos in self.drawPositions:
            util.drawPos(pos)
        #draw line from cur frame to prev frame foreach joint
        for i in range(0,len(self.drawMxs)):
            pointA = util.getPosArray(self.drawMxs[i])
            pointB = self.drawPositions[i]
            util.drawLine(pointA, pointB)

        #util.drawLine(self.drawPositions[3],self.drawPositions[4])




class predictElbowsVel2(object):
    def __init__(self):
        self.transformScale = 1.0
        self.prevTransformList = []
        self.predictionOutputArray = []
        
    
    def operate(self,transformList):
        """
                            ["head", "world"],
                            ["rHand", "world"],    
                            ["lHand", "world"],    
                            ["rForeArm", "world"]   
        """
        #store transformlist for the next frame.
        self.prevTransformList.append(copy.copy(transformList))
        if len(self.prevTransformList)>2:
            del self.prevTransformList[0]


        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        headMx4_1 = self.prevTransformList[0][0]
        rHandMx4_1 = self.prevTransformList[0][1]
        lHandMx4_1 = self.prevTransformList[0][2]
        rForeArmMx4_1 = self.prevTransformList[0][3]     

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)

        headPos_1 = util.getPosArray(headMx4_1) - headPosV3
        rHandPos_1 = util.getPosArray(rHandMx4_1) - headPosV3
        lHandPos_1 = util.getPosArray(lHandMx4_1) - headPosV3

        #if a prediction had been made on the last frame, it was stored
        #in self.predictionOutputArray to use in the next prediction.
        if len(self.predictionOutputArray):
            #print "Previously predicted, and setting to: " + str(self.predictionOutputArray)
            rForeArmPos_1 = self.predictionOutputArray
            self.predictionOutputArray = []
        else:
            rForeArmPos_1 = util.getPosArray(rForeArmMx4_1) - headPosV3
            #print "Using mocap, and setting to: " + str(rForeArmPos_1)


        #send head to origin
        headMx4Origin = copy.copy(headMx4)
        headMx4Origin = util.extractRot(headMx4Origin)

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3

        rHandMx4Origin = copy.copy(rHandMx4)
        rHandMx4Origin = util.setPos(rHandMx4Origin, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4Origin = copy.copy(lHandMx4)
        lHandMx4Origin = util.setPos(lHandMx4Origin, lHandPosV3)

        #send rForeArm to the origin with head offset (we just work with pos)
        rForeArmPosV3 = util.getPosArray(copy.copy(rForeArmMx4))
        rForeArmPosV3 = rForeArmPosV3 - headPosV3

        outputArray = rForeArmPosV3.tolist()
        #print "the output array%s"%(str(outputArray))

        #outputArray = np.array(posList).flatten()

        inputArray = util.getTransformArray(rHandMx4Origin,True).tolist() + util.getRotArray(headMx4Origin).tolist() + util.getTransformArray(lHandMx4Origin,True).tolist()
        inputArray = inputArray + headPos_1.tolist() + rHandPos_1.tolist() + lHandPos_1.tolist() + rForeArmPos_1.tolist()
        #inputArray = inputArray + headPos_1.tolist() + rHandPos_1.tolist() + lHandPos_1.tolist() 

        self.drawMxs = [rHandMx4Origin,headMx4Origin,lHandMx4Origin]

        posList = []
        posList.append(rHandPos_1)
        posList.append(headPos_1)
        posList.append(lHandPos_1)
        posList.append(rForeArmPosV3)
        posList.append(rForeArmPos_1)

        self.drawPositions = posList

        # stuff for recompose
        self.headPosV3 = headPosV3

        self.correct = util.getPosArray(copy.copy(rForeArmMx4))

        #return as python lists
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put rForeArm as offset from extracted head,
        #instead of as offset from head at origin
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(self.headPosV3 + pos)
            pos = []

    def predict(self,predictedOutputArray):
        self.drawRecomposePositions = []
        pos = []
        for i in range(0,len(predictedOutputArray)/3):
            for p in range(i,i+3):
                pos.append(predictedOutputArray[p])
            i=i+3
            self.drawRecomposePositions.append(pos)
            pos = []


    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            util.drawPos(pos,size,magenta)
            #print "predicted %s and correct %s"%(str(pos),str(self.correct))
            util.drawLine(pos,self.correct,1,[1.0,0.0,0.0])
        pointA = np.array([pos[0],pos[1],pos[2]])
        pointB = np.array([self.correct[0],self.correct[1],self.correct[2]])

        errorV3 = pointB-pointA
        errorLength = np.linalg.norm(errorV3)
        
        print "Writing: %s"%(str(errorLength))
        logFile = open('/home/daveotte/predictElbowVel2Error.txt','a')
        logFile.write(str(round(errorLength,3))+'\n')
        logFile.close()

    def draw(self,transformScale):
        for mx in self.drawMxs:
            util.drawMx(mx,transformScale)
        for pos in self.drawPositions:
            util.drawPos(pos)
        #draw line from cur frame to prev frame foreach joint
        for i in range(0,len(self.drawMxs)):
            pointA = util.getPosArray(self.drawMxs[i])
            pointB = self.drawPositions[i]
            util.drawLine(pointA, pointB)

        util.drawLine(self.drawPositions[3],self.drawPositions[4])

'''


