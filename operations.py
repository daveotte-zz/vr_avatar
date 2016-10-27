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



