import numpy as np
import matrixUtil as mxUtil
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *



class predictElbow(object):
    def __init__(self):
        self.transformScale = 1.0
    
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
        size = 6
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 6
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)


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
        size = 6
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 6
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
        size = 6
        mxUtil.drawMx(self.drawRecomposeMx,self.transformScale)
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)

    def drawRecompose(self):
        magenta = [1.0,0.0,1.0]
        size = 6
        mxUtil.drawMx(self.drawRecomposeMx)
        mxUtil.drawPos(self.drawRecomposePos,size,magenta)


    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        mxUtil.drawPos(self.drawPos)

