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
        self.trainingData = App.trainingData
        self.trainingDataConfigs = App.nnDataConfigs
        uic.loadUi('./ui/gui.ui', self)
        self.graphicViewObj = Viewer3DWidget(self)
        self.graphicViewObj.trainingData = self.trainingData
        self.graphicViewObj.testingData = App.testingData
        self.graphicViewObj.transformsFileManager = self.App.transformsFileManager
        self.graphicViewObj.frame = 0
        self.graphicViewerWindow.addWidget(self.graphicViewObj)
        self.setStyleSheet(open('./ui/dark.qss').read())
        self.setup()
        self.show()

        self.drawCurrentFrame()
        sys.exit(app.exec_())
        
        
    def setup(self):
        self.populateConfigurationsList()
        self.populateSceneList()
        self.timeSlider.valueChanged.connect(self.drawCurrentFrame)
        self.graphicViewObj.transformScale = 1.0


        self.graphicViewObj.showSkeleton = self.skeletonCheckbox.isChecked()
        self.skeletonCheckbox.stateChanged.connect(self.setShowSkeleton)

        self.graphicViewObj.showExtractedTransforms = self.extractedCheckbox.isChecked()
        self.extractedCheckbox.stateChanged.connect(self.setShowExtractedTransforms)

        self.graphicViewObj.showManipulatedTransforms = self.manipulatedCheckbox.isChecked()
        self.manipulatedCheckbox.stateChanged.connect(self.setShowManipulatedTransforms)

        self.graphicViewObj.showPredictedTransforms = self.predictedCheckbox.isChecked()
        self.predictedCheckbox.stateChanged.connect(self.setShowPredictedTransforms)

        self.graphicViewObj.showCorrectTransforms = self.correctCheckbox.isChecked()
        self.correctCheckbox.stateChanged.connect(self.setShowCorrectTransforms)

        self.startFrameSpinBox.valueChanged.connect(self.setTimeSliderStart)
        self.endFrameSpinBox.valueChanged.connect(self.setTimeSliderEnd)

        self.trainPushButton.pressed.connect(self.run)
        self.predictPushButton.pressed.connect(self.predict)

        self.graphicViewObj.showGrid = self.gridCheckbox.isChecked()
        self.gridCheckbox.stateChanged.connect(self.setShowGrid)

        self.graphicViewObj.scene = self.getFbxScene()
        self.sceneList.currentItemChanged.connect(self.drawCurrentFrame)

        self.timeLine =  QtCore.QTimeLine(1000)
        #set infinite looping
        self.timeLine.setLoopCount(0)
        self.timeLine.setCurveShape(3)
        self.fps = 24
        
        #set Frame range and time duration
        self.setupTimeLine()
        
        #connect timeSlider to timeLine
        self.timeSlider.sliderPressed.connect(self.stopTimeline)
        self.timeSlider.rangeChanged.connect(self.setupTimeLine)
        self.timeSlider.sliderReleased.connect(self.setTimeLineCurrentFrame)

        #connect timeLine to timeSlider
        self.timeLine.frameChanged.connect(self.setTimeSlider)

        self.playPushButton.pressed.connect(self.startOrStopTimeLine)
        self.timeLine.finished.connect(self.syncPlayButton)


        self.scaleTransforms()
        self.transformScaleSlider.valueChanged.connect(self.scaleTransforms)


    def setTimeLineCurrentFrame(self):
        self.timeLine.setCurrentTime(self.timeForOneFrame*int(self.timeSlider.value()))

    def setupTimeLine(self):
        """
        Use timeSlider to setup frame range
        and time duration of timeLine
        """
        self.setTimeLineFrameRange()
        self.setTimeLineDuration()


    def setTimeLineDuration(self):
        """
        Set QTimeLine duration in milliseconds.
        """
        self.timeLine.setDuration(self.timeLineTimeDuration)

    def setTimeLineFrameRange(self):
        """
        Use timeSlider's min max to set timeLine
        start and end frame.
        """
        self.timeLine.setFrameRange(self.timeSlider.minimum(),self.timeSlider.maximum())

    def stopTimeline(self):
        print "StimeLine State: %s"%(self.timeLine.state())
        if self.timeLine.state() == 2:
            print "Stopping playback."
            self.timeLine.setPaused(True)
            self.playPushButton.setText("Play")


    @property 
    def timeForOneFrame(self):
        """
        The time for one frame.
        """
        return self.timeLineTimeDuration/self.timeLineNumberOfFrames

    @property
    def timeLineTimeDuration(self):
        """
        Return scene duration in milliseconds.
        """
        return self.timeLineNumberOfFrames/self.fps*1000

    @property
    def timeLineNumberOfFrames(self):
        return self.timeSlider.maximum()-self.timeSlider.minimum()
        

    def startOrStopTimeLine(self):
        if str(self.playPushButton.text()) == "Play":
            if self.timeLine.state() == 1:
                self.timeLine.resume()
            else:
                self.timeLine.start()
            self.playPushButton.setText("Stop")
        else:
            self.timeLine.setPaused(True)
            self.playPushButton.setText("Play")

    def syncPlayButton(self):
        if self.timeLine.state() == 0:
            self.playPushButton.setText("Play")
        else:
            self.playPushButton.setText("Stop")

    def setTimeSlider(self):
        print "current frame: %d"%(self.timeLine.currentFrame())
        self.timeSlider.setValue(int(self.timeLine.currentFrame()))

    def run(self):
        self.App.run()

    def predict(self):
        self.App.predict()


        
    def setTimeSliderStart(self):
        self.timeSlider.setMinimum(int(self.startFrameSpinBox.value()))

    def setTimeSliderEnd(self):
        self.timeSlider.setMaximum(int(self.endFrameSpinBox.value()))

    def populateConfigurationsList(self):
        for item in self.trainingDataConfigs.dataObjects:
            self.configurationsList.addItem(item.title)
            
    def populateSceneList(self):
        """
        poplulate list with all fbx files being used
        by current nn configuration
        """
        self.basename2Object = {}
        for item in self.trainingData.fbxScenes:
            self.sceneList.addItem(item.basename)
            #a dict we can use to get the object given the basename
            self.basename2Object[item.basename] = item

        for item in self.App.transformsFileManager.dataObjects:
            self.sceneList.addItem(item.basename)
            #a dict we can use to get the object given the basename
            self.basename2Object[item.basename] = item

    def scaleTransforms(self):
        """
        Apply a scale the matrix axes.
        """
        self.graphicViewObj.transformScale = float(self.transformScaleSlider.value())
        self.graphicViewObj.updateGL()

    def setShowExtractedTransforms(self):
        self.graphicViewObj.showExtractedTransforms = self.extractedCheckbox.isChecked()
        self.graphicViewObj.updateGL()

    def setShowManipulatedTransforms(self):
        self.graphicViewObj.showManipulatedTransforms = self.manipulatedCheckbox.isChecked()
        self.graphicViewObj.updateGL()

    def setShowPredictedTransforms(self):
        self.graphicViewObj.showPredictedTransforms = self.predictedCheckbox.isChecked()
        self.graphicViewObj.updateGL()

    def setShowCorrectTransforms(self):
        self.graphicViewObj.showCorrectTransforms = self.correctCheckbox.isChecked()
        self.graphicViewObj.updateGL()


    def setShowSkeleton(self):
        self.graphicViewObj.showSkeleton = self.skeletonCheckbox.isChecked()
        self.graphicViewObj.updateGL()


    def setShowGrid(self):
        self.graphicViewObj.showGrid = self.gridCheckbox.isChecked()
        self.graphicViewObj.updateGL()


    #Draw entire skeleton
    def drawCurrentFrame(self):
        print 'drawing'
        self.graphicViewObj.scene = self.getFbxScene()

        #TODO-I should only set these when the selected scene changes
        self.startFrameSpinBox.setMinimum(self.graphicViewObj.scene.start)
        self.startFrameSpinBox.setMaximum(self.graphicViewObj.scene.end)
        self.startFrameSpinBox.setValue(self.graphicViewObj.scene.start)

        self.endFrameSpinBox.setMinimum(self.graphicViewObj.scene.start)
        self.endFrameSpinBox.setMaximum(self.graphicViewObj.scene.end)
        self.endFrameSpinBox.setValue(self.graphicViewObj.scene.end)

        self.graphicViewObj.frame = int(self.timeSlider.value())
        self.graphicViewObj.updateGL()

    def getFbxScene(self):
        selectedItems = self.sceneList.selectedItems()
        if len(selectedItems) > 0:
            item = selectedItems[0]
        else:
            item = self.sceneList.item(0)
        print "Scene is now: %s"%str(item.text())
        return self.basename2Object[str(item.text())]

class Viewer3DWidget(QGLWidget):
    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMouseTracking(True)
        # self.setMinimumSize(500, 500)
        self.camera = Camera()
        self.camera.setSceneRadius( 2 )
        self.camera.reset()
        self.camera.setInitial()
        self.isPressed = False
        self.oldx = self.oldy = 0
        format = QGLFormat()
        format.setSampleBuffers(True)
        self.setFormat(format)
        self.transformScale = 1.0



    def paintGL(self):
        glEnable(GL_MULTISAMPLE)
        glMatrixMode(GL_PROJECTION)
        glClearColor(0.1,0.1,0.1,0.0)
        glLoadIdentity()
        
        self.camera.transform()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.showGrid:
            self.drawGrid()
        if self.showSkeleton:
            if self.scene.basename.endswith('.fbx'):
                self.drawSkeleton()
            else:
                self.scene.drawAtFrame(self.frame,self.transformScale)
        
        if self.showExtractedTransforms:
            self.trainingData.drawExtractedTransformsAtFrame(self.scene,self.frame,self.transformScale)

        if self.showManipulatedTransforms:
            self.trainingData.drawManipulatedTransformsAtFrame(self.scene,self.frame,self.transformScale)

        if self.showPredictedTransforms:
            self.testingData.drawPredictedTransformsAtFrame(self.frame)

        if self.showCorrectTransforms:
            self.testingData.drawCorrectTransformsAtFrame(self.frame)
        
        glFlush()

    def resizeGL(self, widthInPixels, heightInPixels):
        self.camera.setViewportDimensions(widthInPixels, heightInPixels)
        glViewport(0, 0, widthInPixels, heightInPixels)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

    def mouseMoveEvent(self, mouseEvent):
        if int(mouseEvent.buttons()) != QtCore.Qt.NoButton :
            # user is dragging
            delta_x = mouseEvent.x() - self.oldx
            delta_y = self.oldy - mouseEvent.y()
            if int(mouseEvent.buttons()) & QtCore.Qt.RightButton :
                self.camera.dollyCameraForward( 3*(delta_x+delta_y), False )

            if int(mouseEvent.buttons()) & QtCore.Qt.LeftButton :
                self.camera.orbit(self.oldx,self.oldy,mouseEvent.x(),mouseEvent.y())
            
            if int(mouseEvent.buttons()) & QtCore.Qt.MidButton :
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

    def drawSkeleton(self):
        """
        Draw skeleton with lines from parent to child.
        Then draw xform of each node in skeleton.
        """
        glColor3f(1.0,1.0,1.0);
        glLineWidth(1)
        glBegin(GL_LINE_STRIP)

        self.drawSkeltonLines(self.scene.jointRoot,0)
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
        #print(lString)
             
        for i in range(pNode.GetChildCount()):
            mx = self.scene.getNpGlobalTransform(pNode.GetName(), self.frame )
            glVertex3fv(mx[3,0:3]) 
            mx = self.scene.getNpGlobalTransform(pNode.GetChild(i).GetName(), self.frame )
            glVertex3fv(mx[3,0:3])  
            if pNode.GetChild(i).GetChildCount():
                self.drawSkeltonLines(pNode.GetChild(i), pDepth + 1)
            else:
                glEnd()
                glBegin(GL_LINE_STRIP)

    def drawSkeletonTransforms(self):
        for nodeName in self.scene.skeletonNodeNameList:
            mxUtil.drawMx(self.scene.getFbxNodeNpTransformAtFrame(nodeName, self.frame),self.transformScale)


    def drawExtractedTransforms(self):
        self.drawMxs(self.extractedTransforms)

    def drawManipulatedTransforms(self):
        self.opObj.transformScale = self.transformScale
        self.opObj.draw()


    def drawMxs(self, transformList):
        for mx in transformList:
            mxUtil.drawMx(mx,self.transformScale)

    def drawGrid(self,size=1000,interval=50):
        """
        Draw a grid on X/Z plane.
        """     
        offset = float(int(size)/2)

        #draw X/Z cardinal axes
        glColor3f(0.3,0.3,0.3);
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(-offset,0.0,0.0)
        glVertex3f(offset,0.0,0.0)
        glVertex3f(0.0,0.0,-offset)
        glVertex3f(0.0,0.0,offset)
        glEnd()
 
        #offset where the grid is drawn to center it.
        glTranslatef(-offset,0,-offset)

        glLineWidth(1)
        glColor3f(0.5,0.5,0.5);
        glBegin(GL_LINES)
        for x in range(0,size+interval,interval):
            glVertex3f(float(x),0.0,0.0)
            glVertex3f(float(x),0.0,float(size))

            glVertex3f(0.0,0.0,float(x))
            glVertex3f(float(size),0.0,float(x))

        glEnd()
        #remove offset
        glTranslatef(offset,0,offset)





