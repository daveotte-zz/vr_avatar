import sys
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtOpenGL import *
from OpenGL.GL import *
from ui.camera import Camera
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

class UI(QMainWindow):
    def __init__(self, App):
        app = QtGui.QApplication(sys.argv)
        super(UI, self).__init__()
        
        uic.loadUi('./ui/gui.ui', self)
        
        ###GRAPHIC WIDGET
        self.graphicsObj = Viewer3DWidget(self)
        #self.graphicsObj.engineDict = self.engineDict
        self.graphicViewerWindow.addWidget(self.graphicsObj)
        self.setStyleSheet(open('./ui/dark.qss').read())
        
        self.graphicsObj.app = App

        self.setup()
        self.show()
        self.drawCurrentFrame()
        sys.exit(app.exec_())
        
        
    def setup(self):
        self.populateEnginesList()
        self.populateSceneList()
        self.timeSlider.valueChanged.connect(self.drawCurrentFrame)
        self.graphicsObj.transformScale = 1.0


        ######SHOW STUFF OR NOT
        self.graphicsObj.showSkeleton = self.skeletonCheckbox.isChecked()
        self.skeletonCheckbox.stateChanged.connect(self.setShowSkeleton)

        self.graphicsObj.showTransforms = self.transformsCheckbox.isChecked()
        self.transformsCheckbox.stateChanged.connect(self.setShowTransforms)

        #self.graphicsObj.showSkeletonRecomposed = self.skeletonRecomposedCheckbox.isChecked()
        #self.skeletonRecomposedCheckbox.stateChanged.connect(self.setShowSkeletonRecomposed)

        self.graphicsObj.showExtracted = self.extractedCheckbox.isChecked()
        self.extractedCheckbox.stateChanged.connect(self.setshowExtracted)

        self.graphicsObj.showManipulated = self.manipulatedCheckbox.isChecked()
        self.manipulatedCheckbox.stateChanged.connect(self.setshowManipulated)

        self.graphicsObj.showPredicted = self.predictedCheckbox.isChecked()
        self.predictedCheckbox.stateChanged.connect(self.setShowPredicted)

        self.graphicsObj.showRecompose = self.recomposeCheckbox.isChecked()
        self.recomposeCheckbox.stateChanged.connect(self.setShowRecompose)

        self.startFrameSpinBox.valueChanged.connect(self.setTimeSliderStart)
        self.endFrameSpinBox.valueChanged.connect(self.setTimeSliderEnd)

        self.graphicsObj.showGrid = self.gridCheckbox.isChecked()
        self.gridCheckbox.stateChanged.connect(self.setShowGrid)

        self.updateInspector()
        #####TRAINING
        self.trainPushButton.pressed.connect(self.run)
        self.terminatePushButton.pressed.connect(self.terminate)

        #####SET WHAT'S CURRENT INITIALLY
        self.graphicsObj.app.setEngine(self.getEngineName())
        self.graphicsObj.app.engine.setScene(self.getSceneName())
        
        ######TIMELINE
        self.timeLine = QtCore.QTimeLine(1000)
        self.timeLine.setLoopCount(0)
        self.timeLine.setCurveShape(3)
        self.fps = 24
        
        #set Frame range and time duration
        self.setupTimeLine()

        ####CONNECT UI ACTIONS TO METHOD CALLS
        self.sceneList.setSortingEnabled(True)
        self.sceneList.itemSelectionChanged.connect(self.updateForSceneChange)
        self.configurationsList.itemSelectionChanged.connect(self.updateForEngineChange)

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

        self.uniformScaleSpinBox.setValue(self.graphicsObj.app.engine.operation.scaleOffset*100)
        self.uniformScale()
        self.uniformScaleSpinBox.valueChanged.connect(self.uniformScale)

        self.headOffsetRotateYSpinBox.setValue(self.graphicsObj.app.engine.operation.rotateHeadDegrees)
        self.rotateHead()
        self.headOffsetRotateYSpinBox.valueChanged.connect(self.rotateHead)

        self.headOffsetTranslateYSpinBox.setValue(self.graphicsObj.app.engine.operation.headTranslateY)
        self.translateHead()
        self.headOffsetTranslateYSpinBox.valueChanged.connect(self.translateHead)
        self.updateForSceneChange()

    def keyPressEvent(self, event):
        print ("Key Pressed.")
        if event.key() == QtCore.Qt.Key_Left or event.key() == QtCore.Qt.Key_N:
            print ("Back 1 frame.")
            self.timeLine.setCurrentTime(self.timeLine.currentTime()-self.timeForOneFrame)
            #self.timeLine.setValue(int(self.timeLine.currentFrame())-1)
        elif event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_M:
            print ("Forward 1 frame.")
            self.timeLine.setCurrentTime(self.timeLine.currentTime()+self.timeForOneFrame)

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
        print ("TimeLine State: %s"%(self.timeLine.state()))
        if self.timeLine.state() == 2:
            print ("Stopping playback.")
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
        Return Scene duration in milliseconds.
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
        print ("current frame: %d"%(self.timeLine.currentFrame()))
        self.timeSlider.setValue(int(self.timeLine.currentFrame()))

    def run(self):
        self.graphicsObj.app.run()

    def terminate(self):
        self.graphicsObj.app.terminate()

    def setTimeSliderStart(self):
        self.timeSlider.setMinimum(int(self.startFrameSpinBox.value()))

    def setTimeSliderEnd(self):
        self.timeSlider.setMaximum(int(self.endFrameSpinBox.value()))

    def populateEnginesList(self):
        self.uiEngineName2ObjectName = {}
        for engine in self.graphicsObj.app.engines:
            self.configurationsList.addItem(engine.title)
            self.uiEngineName2ObjectName[engine.title] = engine.name

        for engineTitle in self.uiEngineName2ObjectName.keys():
            print ("Key is: %s engine name is: %s"%(engineTitle,self.uiEngineName2ObjectName[engineTitle]))
            
    def populateSceneList(self):
        """
        Populate list with all training and testing data (fbx scenes)
        """
        self.uiSceneName2ObjectName = {}
        self.graphicsObj.app.trainingScenes.sort()
        for scene in self.graphicsObj.app.trainingScenes:
            self.sceneList.addItem(scene.title)
            #a dict we can use to get the object name given the title
            self.uiSceneName2ObjectName[scene.title] = scene.title

        self.sceneList.sortItems()


        self.graphicsObj.app.testingScenes.sort()
        for scene in self.graphicsObj.app.testingScenes:
            itemGuiName = scene.title + " TEST"
            self.sceneList.addItem(itemGuiName)
            #a dict we can use to get the object name given the basename
            self.uiSceneName2ObjectName[itemGuiName] = scene.title




    def uniformScale(self):        
        """
        Apply a scale to the matrix axes.
        """
        self.graphicsObj.app.engine.operation.scaleOffset = float(self.uniformScaleSpinBox.value()*.01)
        self.graphicsObj.updateGL()


    def rotateHead(self):        
        """
        Apply a scale the matrix axes.
        """
        self.graphicsObj.app.engine.operation.rotateHeadDegrees = float(self.headOffsetRotateYSpinBox.value())
        self.graphicsObj.updateGL()

    def translateHead(self):        
        """
        Apply a scale the matrix axes.
        """
        self.graphicsObj.app.engine.operation.headTranslateY = float(self.headOffsetTranslateYSpinBox.value())
        self.graphicsObj.updateGL()

    def scaleTransforms(self):
        """
        Uniform scale for vive telemetry
        """
        self.graphicsObj.transformScale = float(self.transformScaleSlider.value())
        self.graphicsObj.updateGL()

    def setshowExtracted(self):
        self.graphicsObj.showExtracted = self.extractedCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def setshowManipulated(self):
        self.graphicsObj.showManipulated = self.manipulatedCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def setShowPredicted(self):
        self.graphicsObj.showPredicted = self.predictedCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def setShowRecompose(self):
        self.graphicsObj.showRecompose = self.recomposeCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def setShowSkeleton(self):
        self.graphicsObj.showSkeleton = self.skeletonCheckbox.isChecked()
        self.graphicsObj.updateGL()

    #def setShowSkeletonRecomposed(self):
    #    self.graphicsObj.showSkeletonRecomposed = self.skeletonRecomposedCheckbox.isChecked()
    #    self.graphicsObj.updateGL()

    def setShowTransforms(self):
        self.graphicsObj.showTransforms = self.transformsCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def setShowGrid(self):
        self.graphicsObj.showGrid = self.gridCheckbox.isChecked()
        self.graphicsObj.updateGL()

    def updateForEngineChange(self):
        self.graphicsObj.app.setEngine(self.getEngineName())
        self.updateInspector()
        self.updateForSceneChange()

    def updateInspector(self):
        self.inspectorText.setText(self.graphicsObj.app.engine.nnConfig.writeWeightsFile)

    def updateForSceneChange(self):
        self.graphicsObj.app.engine.setScene(self.getSceneName())
        self.startFrameSpinBox.setMinimum(self.graphicsObj.app.engine.scene.startTime)
        self.startFrameSpinBox.setMaximum(self.graphicsObj.app.engine.scene.endTime)
        self.startFrameSpinBox.setValue(self.graphicsObj.app.engine.scene.startTime)

        self.endFrameSpinBox.setMinimum(self.graphicsObj.app.engine.scene.startTime)
        self.endFrameSpinBox.setMaximum(self.graphicsObj.app.engine.scene.endTime)
        self.endFrameSpinBox.setValue(self.graphicsObj.app.engine.scene.endTime)
        self.graphicsObj.updateGL()

    #Draw entire skeleton
    def drawCurrentFrame(self):
        self.graphicsObj.app.engine.frame = int(self.timeSlider.value())
        self.graphicsObj.updateGL()

    def getSceneName(self):
        selectedItems = self.sceneList.selectedItems()
        if len(selectedItems) > 0:
            item = selectedItems[0]
        else:
            item = self.sceneList.item(0)
        print ("Scene is now: %s"%str(item.text()))
        sceneName = self.uiSceneName2ObjectName[str(item.text())]
        return sceneName

    def getEngineName(self):
        selectedItems = self.configurationsList.selectedItems()
        i = 0
        for item in selectedItems:
            i = i+1
        if len(selectedItems) > 0:
            item = selectedItems[0]
        else:
            item = self.configurationsList.item(0)
        return self.uiEngineName2ObjectName[str(item.text())]

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
        self.uniformScale = 1.0

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
            self.app.engine.drawSkeleton(self.transformScale,self.showTransforms)
        
        if self.showExtracted:
            self.app.engine.drawExtracted(self.transformScale)

        if self.showManipulated:
            self.app.engine.drawManipulated(self.transformScale)

        if self.showPredicted:
            self.app.engine.drawPredicted(self.transformScale)

        if self.showRecompose:
            self.app.engine.drawRecomposed(self.transformScale)
 
        #if self.showSkeletonRecomposed:
        #    self.app.engine.drawSkeletonRecomposed(self.transformScale,self.showTransforms)
    
        glFlush()

    def resizeGL(self, widthInPixels, heightInPixels):
        print ("Resize being called.")
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
        print ("double click")

    def mousePressEvent(self, e):
        print ("mouse press")
        self.isPressed = True

    def mouseReleaseEvent(self, e):
        print ("mouse release")
        self.isPressed = False

    def drawSkeleton(self):
        """
        Draw skeleton with lines from parent to child.
        Then draw xform of each node in skeleton.
        """
        self.app.engine.drawSkeleton(self.transformScale,self.showTransforms)

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





