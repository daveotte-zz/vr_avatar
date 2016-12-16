import numpy as np
import matrixUtil as mxUtil
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import copy

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
        headPosV3 = mxUtil.getPosArray(headMx4)


        #send head to origin
        headMx4 = mxUtil.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = mxUtil.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = mxUtil.setPos(lHandMx4, lHandPosV3)

        #send rForeArm to the origin with head offset
        posList = []
        for i in range(3,len(transformList)):
            #convert list of transforms to list of positions
            pos = mxUtil.getPosArray(transformList[i])
            pos = pos - headPosV3
            posList.append(pos)

        outputArray = []
        #convert numpy 38,3 list to flat python list
        for p in posList:
            outputArray = outputArray + p.tolist()

        #convert back to flat numpy array
        #outputArray = np.array(posList).flatten()

        inputArray = mxUtil.getTransformArray(rHandMx4).tolist() + mxUtil.getRotArray(headMx4).tolist() + mxUtil.getTransformArray(lHandMx4).tolist()


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
            mxUtil.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            mxUtil.drawPos(pos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        for pos in self.drawPositions:
            mxUtil.drawPos(pos)


class predictElbow(object):
    def __init__(self):
        self.transformScale = 1.0
        self.rShldrPos = [0.0,0.0,0.0]
        self.rHandPos = [0.0,0.0,0.0]
    
    def operate(self,transformList):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],    
        """
        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rForeArmMx4 = transformList[3]

        self.correct = mxUtil.getPosArray(rForeArmMx4)

        #get head position v3
        headPosV3 = mxUtil.getPosArray(headMx4)

        #send head to origin
        headMx4 = mxUtil.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = mxUtil.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = mxUtil.setPos(lHandMx4, lHandPosV3)

        #send rForeArm to the origin with head offset
        rForeArmPosV3 = mxUtil.getPosArray(rForeArmMx4)
        rForeArmPosV3 = rForeArmPosV3 - headPosV3
        rForeArmMx4 = mxUtil.setPos(rForeArmMx4, rForeArmPosV3)

        inputArray = mxUtil.getTransformArray(rHandMx4).tolist() + mxUtil.getRotArray(headMx4).tolist() + mxUtil.getTransformArray(lHandMx4).tolist()

        outputArray = mxUtil.getPosArray(rForeArmMx4).tolist()      

        self.drawMxs = [rHandMx4,headMx4,lHandMx4,rForeArmMx4]
        self.drawPos = outputArray

        # stuff for recompose
        self.headPosV3 = headPosV3
        self.rForeArmPosV3 = rForeArmPosV3

        #return as python lists...apparently.
        return inputArray, outputArray

    def recompose(self,predictedOutputArray):
        """
        Put the outputArray back into the space of the extracted
        transforms. Allows seeing the predictions in place.
        """
        #put rForeArm as offset from extracted head,
        #instead of as offset from head at origin
        self.drawRecomposePos = self.headPosV3 + predictedOutputArray

    def predict(self,predictedOutputArray):
        self.drawRecomposePos = predictedOutputArray

    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)
        mxUtil.drawLine(self.drawRecomposePos,self.correct,1,[1.0,0.0,0.0])
        pointA = np.array([self.drawRecomposePos[0],self.drawRecomposePos[1],self.drawRecomposePos[2]])
        pointB = np.array([self.correct[0],self.correct[1],self.correct[2]])

        errorV3 = pointB-pointA
        errorLength = np.linalg.norm(errorV3)
        
        #print "Writing: %s"%(str(errorLength))
        #logFile = open('/home/daveotte/predictElbowError.txt','a')
        #logFile.write(str(round(errorLength,3))+'\n')
        #logFile.close()


        mxUtil.drawLine(self.rShldrPos,self.drawRecomposePos)
        mxUtil.drawLine(self.rHandPos,self.drawRecomposePos)
        #rHandPos = mxUtil.getPosArray(self.scene.getFbxNodeNpTransformAtFrame('rHand', self.frame))
        #pointB = [rHandPos[0],rHandPos[1],rHandPos[2]]
        #mxUtil.drawLine(pointA,pointB)      


    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        mxUtil.drawPos(self.drawPos)



class predictShldr(object):
    def __init__(self):
        self.transformScale = 1.0

    def operate(self,transformList):
        headMx4 = transformList[0]
        rHandMx4 = transformList[1]
        lHandMx4 = transformList[2]
        rShldrMx4 = transformList[3]

        #get head position v3
        headPosV3 = mxUtil.getPosArray(headMx4)

        #send head to origin
        headMx4 = mxUtil.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = mxUtil.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = mxUtil.setPos(lHandMx4, lHandPosV3)

        #send rShldr to the origin with head offset
        rShldrPosV3 = mxUtil.getPosArray(rShldrMx4)
        rShldrPosV3 = rShldrPosV3 - headPosV3
        rShldrMx4 = mxUtil.setPos(rShldrMx4, rShldrPosV3)

        inputArray = mxUtil.getTransformArray(rHandMx4).tolist() + mxUtil.getRotArray(headMx4).tolist() + mxUtil.getTransformArray(lHandMx4).tolist()

        outputArray = mxUtil.getPosArray(rShldrMx4).tolist()      

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
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        mxUtil.drawPos(self.drawPos)






def posFromRot (transformList):
    """
    transformList[0]: extract rotation
    transformList[1]: apply to extracted rotation.
    """

    #process the xforms
    mxA = mxUtil.extractRot(transformList[0])
    mxB = mxUtil.extractPos(transformList[1])
    mxC = mxUtil.multiply(mxA,mxB)

    #rotation of mxA
    inputArray = mxUtil.getRotArray(mxA)
    outputArray = mxUtil.getPosArray(mxC)

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
        headPosV3 = mxUtil.getPosArray(headMx4)

        #send head to origin
        headMx4 = mxUtil.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = mxUtil.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = mxUtil.setPos(lHandMx4, lHandPosV3)

        #send hip to the origin with head offset
        hipPosV3 = mxUtil.getPosArray(hipMx4)
        hipPosV3 = hipPosV3 - headPosV3
        hipMx4 = mxUtil.setPos(hipMx4, hipPosV3)

        inputArray = mxUtil.getTransformArray(rHandMx4).tolist() + mxUtil.getRotArray(headMx4).tolist() + mxUtil.getTransformArray(lHandMx4).tolist()

        outputArray = mxUtil.getTransformArray(hipMx4).tolist()      

        self.drawMxs = [rHandMx4,headMx4,lHandMx4,hipMx4]
        #draw output hip position
        self.drawPos = mxUtil.getPosArray(hipMx4).tolist()

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
        predictedMx =  mxUtil.listToNumpyMx(predictedOutputArray)
        self.drawRecomposePos = self.headPosV3 + mxUtil.getPosArray(predictedMx)
        self.drawRecomposeMx = mxUtil.setPos(predictedMx, self.drawRecomposePos)

    def predict(self,predictedOutputArray): 
        predictedMx =  mxUtil.listToNumpyMx(predictedOutputArray)
        self.drawRecomposeMx = predictedMx                  
        self.drawRecomposePos = mxUtil.getPosArray(self.drawRecomposeMx) 


    def drawPredict(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        mxUtil.drawMx(self.drawRecomposeMx,self.transformScale)
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        mxUtil.drawMx(self.drawRecomposeMx)
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        mxUtil.drawPos(self.drawPos)



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
        headPosV3 = mxUtil.getPosArray(headMx4)

        headPos_1 = mxUtil.getPosArray(headMx4_1) - headPosV3
        rHandPos_1 = mxUtil.getPosArray(rHandMx4_1) - headPosV3
        lHandPos_1 = mxUtil.getPosArray(lHandMx4_1) - headPosV3



        #rForeArmPos_1 = mxUtil.getPosArray(rForeArmMx4_1) - headPosV3

        #send head to origin
        headMx4Origin = copy.copy(headMx4)
        headMx4Origin = mxUtil.extractRot(headMx4Origin)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3

        rHandMx4Origin = copy.copy(rHandMx4)
        rHandMx4Origin = mxUtil.setPos(rHandMx4Origin, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4Origin = copy.copy(lHandMx4)
        lHandMx4Origin = mxUtil.setPos(lHandMx4Origin, lHandPosV3)

        #send rForeArm to the origin with head offset (we just work with pos)
        rForeArmPosV3 = mxUtil.getPosArray(copy.copy(rForeArmMx4))
        rForeArmPosV3 = rForeArmPosV3 - headPosV3

        outputArray = rForeArmPosV3.tolist()
        #print "the output array%s"%(str(outputArray))

        #outputArray = np.array(posList).flatten()

        inputArray = mxUtil.getTransformArray(rHandMx4Origin,True).tolist() + mxUtil.getRotArray(headMx4Origin).tolist() + mxUtil.getTransformArray(lHandMx4Origin,True).tolist()
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

        self.correct = mxUtil.getPosArray(copy.copy(rForeArmMx4))

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
            mxUtil.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            mxUtil.drawPos(pos,size,magenta)
            #print "predicted %s and correct %s"%(str(pos),str(self.correct))
            mxUtil.drawLine(pos,self.correct,1,[1.0,0.0,0.0])
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
            mxUtil.drawMx(mx,self.transformScale)
        for pos in self.drawPositions:
            mxUtil.drawPos(pos)
        #draw line from cur frame to prev frame foreach joint
        for i in range(0,len(self.drawMxs)):
            pointA = mxUtil.getPosArray(self.drawMxs[i])
            pointB = self.drawPositions[i]
            mxUtil.drawLine(pointA, pointB)

        #mxUtil.drawLine(self.drawPositions[3],self.drawPositions[4])




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
        headPosV3 = mxUtil.getPosArray(headMx4)

        headPos_1 = mxUtil.getPosArray(headMx4_1) - headPosV3
        rHandPos_1 = mxUtil.getPosArray(rHandMx4_1) - headPosV3
        lHandPos_1 = mxUtil.getPosArray(lHandMx4_1) - headPosV3

        #if a prediction had been made on the last frame, it was stored
        #in self.predictionOutputArray to use in the next prediction.
        if len(self.predictionOutputArray):
            #print "Previously predicted, and setting to: " + str(self.predictionOutputArray)
            rForeArmPos_1 = self.predictionOutputArray
            self.predictionOutputArray = []
        else:
            rForeArmPos_1 = mxUtil.getPosArray(rForeArmMx4_1) - headPosV3
            #print "Using mocap, and setting to: " + str(rForeArmPos_1)


        #send head to origin
        headMx4Origin = copy.copy(headMx4)
        headMx4Origin = mxUtil.extractRot(headMx4Origin)

        #send rHand to the origin with head offset
        rHandPosV3 = mxUtil.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3

        rHandMx4Origin = copy.copy(rHandMx4)
        rHandMx4Origin = mxUtil.setPos(rHandMx4Origin, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = mxUtil.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4Origin = copy.copy(lHandMx4)
        lHandMx4Origin = mxUtil.setPos(lHandMx4Origin, lHandPosV3)

        #send rForeArm to the origin with head offset (we just work with pos)
        rForeArmPosV3 = mxUtil.getPosArray(copy.copy(rForeArmMx4))
        rForeArmPosV3 = rForeArmPosV3 - headPosV3

        outputArray = rForeArmPosV3.tolist()
        #print "the output array%s"%(str(outputArray))

        #outputArray = np.array(posList).flatten()

        inputArray = mxUtil.getTransformArray(rHandMx4Origin,True).tolist() + mxUtil.getRotArray(headMx4Origin).tolist() + mxUtil.getTransformArray(lHandMx4Origin,True).tolist()
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

        self.correct = mxUtil.getPosArray(copy.copy(rForeArmMx4))

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
            mxUtil.drawPos(pos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 9
        for pos in self.drawRecomposePositions:
            mxUtil.drawPos(pos,size,magenta)
            #print "predicted %s and correct %s"%(str(pos),str(self.correct))
            mxUtil.drawLine(pos,self.correct,1,[1.0,0.0,0.0])
        pointA = np.array([pos[0],pos[1],pos[2]])
        pointB = np.array([self.correct[0],self.correct[1],self.correct[2]])

        errorV3 = pointB-pointA
        errorLength = np.linalg.norm(errorV3)
        
        print "Writing: %s"%(str(errorLength))
        logFile = open('/home/daveotte/predictElbowVel2Error.txt','a')
        logFile.write(str(round(errorLength,3))+'\n')
        logFile.close()

    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        for pos in self.drawPositions:
            mxUtil.drawPos(pos)
        #draw line from cur frame to prev frame foreach joint
        for i in range(0,len(self.drawMxs)):
            pointA = mxUtil.getPosArray(self.drawMxs[i])
            pointB = self.drawPositions[i]
            mxUtil.drawLine(pointA, pointB)

        mxUtil.drawLine(self.drawPositions[3],self.drawPositions[4])
