import numpy as np


def fbxMxtoList(fbxMx):
	"""
	Convert an fbx matrix to a python list.
	"""
	mxList = []
	#height of a column is the number of rows
	rowCount = len(list(fbxMx.GetColumn(0)))
	for r in range(rowCount):
		mxList.append(list(fbxMx.GetRow(r)))
	return mxList

def listToNumpyMx(mxList):
	"""
	Convert a normal python list to numpy matrix
	"""
	return np.matrix(mxList)

def fbxMxtoNumpyMx(fbxMx):
	"""
	Convert an FBX matrix to a numpy matrix.
	"""
	return listToNumpyMx(fbxMxtoList(fbxMx))

def extractPos(mx4):
	"""
	Extract position by setting rotation to mx4 identity.
	"""
	return copyRot(np.identity(4),mx4)

def extractRot(mx4):
	"""
	Extract rotation by setting position to 0,0,0.
	"""
	return copyPos(np.identity(4),mx4)

def copyPos(mx4Src, mx4Dest):
	"""
	Copy pos mx4 elements from mxSrc
	to mxDest.
	"""
	mx4Dest[3:4,0:3] = mx4Src[3:4,0:3]
	return mx4Dest

def copyRot(mx4Src, mx4Dest):
	"""
	Copy rot mx4 elements from mxSrc
	to mxDest.
	"""
	mx4Dest[0:3,0:3] = mx4Src[0:3,0:3]
	return mx4Dest

def multiply(mx4A, mx4B):
	"""
	Multiply two numpy matrices.
	"""
	return mx4A*mx4B

def getRotArray(mx4):
	"""
	Extract 3x3 rot matrix, flatten, and return as
	a numpy array (instead of matrix)
	"""
	return mx4[0:3,0:3].flatten().getA()[0]

def getPosArray(mx4):
	"""
	Extract v3 position, and return as
	a numpy array.
	"""
	return mx4[3:4,0:3].flatten().getA()[0]