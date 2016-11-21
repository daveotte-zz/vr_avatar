import numpy as np
import matrixUtil as mxUtil
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *

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

def jointsAsHMDandControllers(transformList):
    """
                            ["head", "world"],0
                            ["rHand", "world"],1    
                            ["rForeArm", "world"],2
    """
    headMx4 = transformList[0]
    rHandMx4 = transformList[1]
    rForeArmMx4 = transformList[2]

    #get local offset from head
    rHandMx4LocalOffset = mxUtil.multiply(rHandMx4,headMx4.I)
    rForeArmMx4LocalOffset = mxUtil.multiply(rForeArmMx4,headMx4.I)

    #send head to origin
    headMx4AtOrigin = mxUtil.extractRot(headMx4)

    #apply local offset to head at origin
    rHandMx4 = mxUtil.multiply(rHandMx4LocalOffset,headMx4AtOrigin)
    rForeArmMx4 = mxUtil.multiply(rForeArmMx4LocalOffset,headMx4AtOrigin)

    #input is headAtOrigin rotation, rHandMx4 transform
    #output is rForeArmMx4 pos

    #head transform array

    inputArray = mxUtil.getRotArray(headMx4AtOrigin).tolist() + mxUtil.getTransformArray(rHandMx4).tolist()
    outputArray = mxUtil.getPosArray(rForeArmMx4).tolist()    

    return inputArray, outputArray

def predictHipFromHeadAndHands(transformList):
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
    outputArray = []
    outputArray.append(mxUtil.getPosArray(rForeArmMx4).tolist()[2])

    return inputArray, outputArray

class predictElbow(object):
    def __init__(self):
        self.transformScale = 1.0
    
    def operation(self,transformList):
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
        outputArray = []

        outputArray = mxUtil.getPosArray(rForeArmMx4).tolist()      

        self.drawMxs = [rHandMx4,headMx4,lHandMx4,rForeArmMx4]
        self.drawPos = outputArray
        return inputArray, outputArray

    def draw(self):
        for mx in self.drawMxs:
            mxUtil.drawMx(mx,self.transformScale)
        mxUtil.drawPos(self.drawPos)



