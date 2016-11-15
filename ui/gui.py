import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import numpy as np
from camera import Camera
import re
import lib.matrixUtil as mxUtil

class UI(QtGui.QMainWindow):
    def __init__(self, App):
        app = QtGui.QApplication(sys.argv)
        super(UI, self).__init__()
        self.App = App
        self.nnData = App.nnData
        self.nnDataConfigs = App.nnDataConfigs
        uic.loadUi('./ui/gui.ui', self)
        self.graphicViewObj = Viewer3DWidget(self)
        self.graphicViewObj.nnData = self.nnData
        self.graphicViewerWindow.addWidget(self.graphicViewObj)
        self.setStyleSheet(open('./ui/dark.qss').read())
        self.setup()
        self.show()
        self.frame = 0

        self.drawCurrentFrame()
        sys.exit(app.exec_())
        
        
    def setup(self):
        self.populateConfigurationsList()
        self.populateFbxSceneList()
        self.timeSlider.valueChanged.connect(self.drawCurrentFrame)

        self.graphicViewObj.transformScale = 1.0
        self.transformScaleSlider.valueChanged.connect(self.scaleTransforms)

        selectedItems = self.fbxSceneList.selectedItems()
        if len(selectedItems) > 0:
            item = selectedItems[0]
        else:
            item = self.fbxSceneList.item(0)

        self.fbxSceneList.currentItemChanged.connect(self.drawCurrentFrame)

        self.graphicViewObj.showSkeleton = self.skeletonCheckbox.checkState()
        self.skeletonCheckbox.stateChanged.connect(self.setShowSkeleton)

        self.graphicViewObj.showExtractedTransforms = self.extractedCheckbox.checkState()
        self.extractedCheckbox.stateChanged.connect(self.setShowExtractedTransforms)

        self.graphicViewObj.showManipulatedTransforms = self.manipulatedCheckbox.checkState()
        self.manipulatedCheckbox.stateChanged.connect(self.setShowManipulatedTransforms)

    def populateConfigurationsList(self):
        for item in self.nnDataConfigs.dataObjects:
            self.configurationsList.addItem(item.title)
            
    def populateFbxSceneList(self):
        """
        poplulate list with all fbx files being used
        by current nn configuration
        """
        self.fbxBasename2Object = {}
        for item in self.nnData.fbxScenes:
            self.fbxSceneList.addItem(item.basename)
            #a dict we can use to get the object given the basename
            self.fbxBasename2Object[item.basename] = item

    def scaleTransforms(self):
        """
        Apply a scale the matrix axes.
        """
        self.graphicViewObj.transformScale = float(self.transformScaleSlider.value())
        self.graphicViewObj.updateGL()

    def setShowExtractedTransforms(self):
        self.graphicViewObj.showExtractedTransforms = self.extractedCheckbox.checkState()
        self.graphicViewObj.updateGL()

    def setShowManipulatedTransforms(self):
        self.graphicViewObj.showManipulatedTransforms = self.manipulatedCheckbox.checkState()
        self.graphicViewObj.updateGL()


    def setShowSkeleton(self):
        self.graphicViewObj.showSkeleton = self.skeletonCheckbox.checkState()
        self.graphicViewObj.updateGL()


    #Draw entire skeleton
    def drawCurrentFrame(self):
        print 'drawing'
        self.graphicViewObj.fbxScene            = self.getFbxScene()
        self.graphicViewObj.frame               = int(self.timeSlider.value())
        #self.App.nnData.getExtractedSceneTransformsAtFrame(self.graphicViewObj.fbxScene, self.graphicViewObj.frame)
        #self.graphicViewObj.extractedTransforms = \
        #        self.App.nnData.getExtractedSceneTransformsAtFrame(self.graphicViewObj.fbxScene, self.graphicViewObj.frame)
        #self.graphicViewObj.opObj = self.App.nnData.getOpObjAtFrame(self.graphicViewObj.fbxScene, self.graphicViewObj.frame)
        self.graphicViewObj.updateGL()

    def getFbxScene(self):
        selectedItems = self.fbxSceneList.selectedItems()
        if len(selectedItems) > 0:
            item = selectedItems[0]
        else:
            item = self.fbxSceneList.item(0)
        print "Scene is now: %s"%str(item.text())
        return self.fbxBasename2Object[str(item.text())]

class Viewer3DWidget(QGLWidget):
    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMouseTracking(True)
        # self.setMinimumSize(500, 500)
        self.camera = Camera()
        self.camera.setSceneRadius( 2 )
        self.camera.reset()
        self.isPressed = False
        self.oldx = self.oldy = 0
        format = QGLFormat()
        format.setSampleBuffers(True)
        self.setFormat(format)
        self.transformScale = 1.0


    def paintGL(self):
        glEnable(GL_MULTISAMPLE)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self.camera.transform()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        '''
        glDepthFunc( GL_LEQUAL )
        glEnable( GL_DEPTH_TEST )
        glEnable( GL_CULL_FACE )
        glFrontFace( GL_CCW )
        glDisable( GL_LIGHTING )
        glShadeModel( GL_FLAT )
        '''

        if self.showSkeleton:
            self.drawSkeleton()

        if self.showExtractedTransforms:
            self.nnData.drawExtractedTransformsAtFrame(self.fbxScene,self.frame,self.transformScale)

        if self.showManipulatedTransforms:
            self.nnData.drawManipulatedTransformsAtFrame(self.fbxScene,self.frame,self.transformScale)
        
        glFlush()

    def resizeGL(self, widthInPixels, heightInPixels):
        self.camera.setViewportDimensions(widthInPixels, heightInPixels)
        glViewport(0, 0, widthInPixels, heightInPixels)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        # glMatrixMode(GL_PROJECTION)
        # glLoadIdentity()

    def mouseMoveEvent(self, mouseEvent):
        if int(mouseEvent.buttons()) != QtCore.Qt.NoButton :
            # user is dragging
            delta_x = mouseEvent.x() - self.oldx
            delta_y = self.oldy - mouseEvent.y()
            if int(mouseEvent.buttons()) & QtCore.Qt.LeftButton :
                if int(mouseEvent.buttons()) & QtCore.Qt.MidButton :
                    self.camera.dollyCameraForward( 3*(delta_x+delta_y), False )
                else:
                    self.camera.orbit(self.oldx,self.oldy,mouseEvent.x(),mouseEvent.y())
            elif int(mouseEvent.buttons()) & QtCore.Qt.MidButton :
                self.camera.translateSceneRightAndUp( delta_x, delta_y )
            self.update()
        self.oldx = mouseEvent.x()
        self.oldy = mouseEvent.y()

    def mouseDoubleClickEvent(self, mouseEvent):
        print "double click"

    def mousePressEvent(self, e):
        print "mouse press"
        self.isPressed = True

    def mouseReleaseEvent(self, e):
        print "mouse release"
        self.isPressed = False

    def drawSkeleton(self,):
        """
        Draw skeleton with lines from parent to child.
        Then draw xform of each node in skeleton.
        """
        glColor3f(1.0,1.0,1.0);
        glBegin(GL_LINE_STRIP)
        self.drawSkeltonLines(self.fbxScene.jointRoot,0)
        glEnd()
        self.drawSkeletonTransforms()

    def drawSkeltonLines(self, pNode, pDepth):
        """
        Walk hierarchy to draw lines from parent to children
        by walking hierarchy.
        """
        lString = ""
        for i in range(pDepth):
            lString += "     "
        lString += pNode.GetName()
        print(lString)
             
        for i in range(pNode.GetChildCount()):
            mx = self.fbxScene.getNpGlobalTransform(pNode.GetName(), self.frame )
            glVertex3fv(mx[3,0:3]) 
            mx = self.fbxScene.getNpGlobalTransform(pNode.GetChild(i).GetName(), self.frame )
            glVertex3fv(mx[3,0:3])  
            if pNode.GetChild(i).GetChildCount():
                self.drawSkeltonLines(pNode.GetChild(i), pDepth + 1)
            else:
                glEnd()
                glBegin(GL_LINE_STRIP)

    def drawSkeletonTransforms(self):
        for nodeName in self.fbxScene.skeletonNodeNameList:
            mxUtil.drawMx(self.fbxScene.getFbxNodeNpTransformAtFrame(nodeName, self.frame),self.transformScale)


    def drawExtractedTransforms(self):
        self.drawMxs(self.extractedTransforms)

    def drawManipulatedTransforms(self):
        self.opObj.transformScale = self.transformScale
        self.opObj.draw()

        

    def drawMxs(self, transformList):
        for mx in transformList:
            mxUtil.drawMx(mx,self.transformScale)





