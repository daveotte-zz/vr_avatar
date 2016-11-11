import numpy as np
import matrixUtil as mx

def posFromRot (transformList):
	"""
	transformList[0]: extract rotation
	transformList[1]: apply to extracted rotation.
	"""

	#process the xforms
	mxA = mx.extractRot(transformList[0])
	mxB = mx.extractPos(transformList[1])
	mxC = mx.multiply(mxA,mxB)

	#rotation of mxA
	inputArray = mx.getRotArray(mxA)
	outputArray = mx.getPosArray(mxC)

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
	rHandMx4LocalOffset = mx.multiply(rHandMx4,headMx4.I)
	rForeArmMx4LocalOffset = mx.multiply(rForeArmMx4,headMx4.I)

	#send head to origin
	headMx4AtOrigin = mx.extractRot(headMx4)

	#apply local offset to head at origin
	rHandMx4 = mx.multiply(rHandMx4LocalOffset,headMx4AtOrigin)
	rForeArmMx4 = mx.multiply(rForeArmMx4LocalOffset,headMx4AtOrigin)

	#input is headAtOrigin rotation, rHandMx4 transform
	#output is rForeArmMx4 pos

	#head transform array

	inputArray = mx.getRotArray(headMx4AtOrigin).tolist() + mx.getTransformArray(rHandMx4).tolist()
	outputArray = mx.getPosArray(rForeArmMx4).tolist()	

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
	headPosV3 = mx.getPosArray(headMx4)

	#send head to origin
	headMx4 = mx.extractRot(headMx4)

	#send rHand to the origin with head offset
	rHandPosV3 = mx.getPosArray(rHandMx4)
	rHandPosV3 = rHandPosV3 - headPosV3
	rHandMx4 = mx.setPos(rHandMx4, rHandPosV3)
	
	#send lHand to the origin with head offset
	lHandPosV3 = mx.getPosArray(lHandMx4)
	lHandPosV3 = lHandPosV3 - headPosV3
	lHandMx4 = mx.setPos(lHandMx4, lHandPosV3)

	#send rForeArm to the origin with head offset
	rForeArmPosV3 = mx.getPosArray(rForeArmMx4)
	rForeArmPosV3 = rForeArmPosV3 - headPosV3
	rForeArmMx4 = mx.setPos(rForeArmMx4, rForeArmPosV3)

	inputArray = mx.getTransformArray(rHandMx4).tolist() + mx.getRotArray(headMx4).tolist() + mx.getTransformArray(lHandMx4).tolist()
	outputArray = []
	outputArray.append(mx.getPosArray(rForeArmMx4).tolist()[2])

	return inputArray, outputArray

