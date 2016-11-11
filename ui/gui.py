import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
import numpy as np
from camera import Camera
import re

class UI(QtGui.QMainWindow):
    def __init__(self, App):
        app = QtGui.QApplication(sys.argv)
        super(UI, self).__init__()
        self.App = App
        uic.loadUi('./ui/gui.ui', self)
        self.graphicViewObj = Viewer3DWidget(self)
        self.graphicViewerWindow.addWidget(self.graphicViewObj)
        self.setStyleSheet(open('./ui/dark.qss').read())
        self.setup()
        self.show()
        self.drawCurrentFrame()
        sys.exit(app.exec_())
        
        
    def setup(self):
        self.populateConfigurationsList()
        self.populateFbxSceneList()
        self.timeSlider.valueChanged.connect(self.drawCurrentFrame)

    def populateConfigurationsList(self):
        for item in self.App.nnDataConfigs.dataObjects:
            self.configurationsList.addItem(item.title)
            

    def populateFbxSceneList(self):
        """
        poplulate list with all fbx files being used
        by current nn configuration
        """
        self.fbxBasename2Object = {}
        for item in self.App.nnDataObj.fbxScenes:
            self.fbxSceneList.addItem(item.basename)
            #a dict we can use to get the object given the basename
            self.fbxBasename2Object[item.basename] = item


    
    def drawCurrentFrame(self):
        print 'drawing'
        selectedItems = self.fbxSceneList.selectedItems()
        if len(selectedItems) > 0:

            item = selectedItems[0]
        else:
            item = self.fbxSceneList.item(0)
        self.graphicViewObj.transforms = self.App.nnDataObj.getSceneTransformsAtFrame(self.fbxBasename2Object[str(item.text())],int(self.timeSlider.value()))
        self.graphicViewObj.updateGL()
    
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
        
        self.drawMxs()
        self.drawMx(np.identity(4))



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

    def drawMxs(self):
        for mx in self.transforms:
            self.drawMx(mx)

    def drawMx(self,mx):
        """
        Draw a numpy matrix.
        """
        axisColor = {}
        axisColor[0] = [1.0, 0.0, 0.0]
        axisColor[1] = [0.0, 1.0, 0.0]
        axisColor[2] = [0.0, 0.0, 1.0]
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(mx.item(12),mx.item(13),mx.item(15))


        for i in range(3):
            c = axisColor[i]
            glLineWidth(3)
            glBegin(GL_LINE_STRIP)
            
            glColor3f(c[0],c[1],c[2]);
            glVertex3fv([0.0,0.0,0.0])
            glVertex3fv(mx[i,0:3])
            glEnd()

        glLoadIdentity()




