import os
import re
import numpy as np
from PyQt4.QtOpenGL import *
from OpenGL.GL import *

pyListType = type([])
npListType = type(np.arange(1))
npMxType = type(np.matrix(1))



class colors(object):
    """
    An object with color names as attributes, and values that
    correspond to RGB v3 values.
    """
    def __init__(self):
        self.magenta    = [1.0,0.0,1.0]
        self.white      = [1.0,1.0,1.0]
        self.blue       = [0.0,0.0,1.0]

color = colors()


def predict(model,inputData):
    return model.predict_on_batch(inputData)

def camel2Title(camel):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', camel).title()#.replace('Predict ', '')


def getJsonFile():
    '''
    Return abs path to json file.
    '''
    return os.path.dirname(__file__) + '/config.json'


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
    return np.matrix(mxList).reshape(4,4)

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

def getTransformArray(mx4,exclude4thColumn=False):
    """
    Convert mx4 to np array of 16 numbers.
    """
    if exclude4thColumn:
        return mx4[0:4,0:3].flatten().getA()[0]
    else:
        return mx4.flatten().getA()[0]

def setPos(mx4, v3):
    """
    Set mx4's pos by a vector.
    """
    mx4[3:4,0:3] = v3
    return mx4

def setRot(mx4,v9):
    """
    Set mx4's rot by a list of 9 numbers.
    """
    mx4[0:1,0:3] = [v9[0],v9[1],v9[2]]
    mx4[1:2,0:3] = [v9[3],v9[4],v9[5]]
    mx4[2:3,0:3] = [v9[6],v9[7],v9[8]]
    return mx4

def addPosToMx4(mx4,v3):
    mx4[3:4,0:3]=getPosArray(mx4)+v3
    return mx4

def drawMxs(mxs,transformScale):
    for mx in mxs:
        drawMx(mx,transformScale)

def drawMx(mx,transformScale=1.0):
    """
    Draw a numpy matrix.
    """
    axisColor = {}
    #TODO-make these properties on this class, or utilMatrix
    axisColor[0] = [1.0, 0.0, 0.0]
    axisColor[1] = [0.0, 1.0, 0.0]
    axisColor[2] = [0.0, 0.0, 1.0]
    glMatrixMode(GL_MODELVIEW)
    glLoadMatrixf(mx)
    #glTranslatef(mx.item(12),mx.item(13),mx.item(15))

    mx = np.matrix(np.identity(4))
    scale = 1+transformScale*0.3
    mx[0:1,0:1] = scale
    mx[1:2,1:2] = scale
    mx[2:3,2:3] = scale



    for i in range(3):
        c = axisColor[i]
        glLineWidth(3)
        glBegin(GL_LINE_STRIP)
        
        glColor3f(c[0],c[1],c[2]);
        glVertex3fv([0.0,0.0,0.0])
        glVertex3fv(mx[i,0:3])
        glEnd()

    glLoadIdentity()    

def drawPoints(v3List,size=6,color=[1.0,1.0,0.0]):
    for point in v3List:
        drawPoint(point,size,color)


def drawPoint(v3,size=6,color=[1.0,1.0,0.0]):
    """
    Draw a vector (a dot) given
    x,y,z
    """
    glPointSize(int(size))
    glBegin(GL_POINTS)
    glColor3f(color[0],color[1],color[2])
    glVertex3f(v3[0],v3[1],v3[2]);
    glEnd()

def drawLine(pointA, pointB, size=1,color=[1.0,1.0,1.0]):
    """
    Draw a line (a dot) given two v3's
    """
    glLineWidth(size)
    glBegin(GL_LINE_STRIP)
    
    glColor3f(color[0],color[1],color[2]);
    glVertex3fv([pointA[0],pointA[1],pointA[2]])
    glVertex3fv([pointB[0],pointB[1],pointB[2]])
    glEnd()

def identity():
    return np.matrix(np.identity(4))

def orthonormalize(mx):
    mat = mx[0:3,0:3]
    (u,_,v) = np.linalg.svd(mat,False)
    mat = u.dot(v)
    mx[0:3,0:3] = mat
    return mx
