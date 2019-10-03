import numpy as np
import lib.util as util
from PyQt5.QtOpenGL import *
from OpenGL.GL import *
import copy
from rig.joints import *
from keras.models import model_from_json
import json

class operation:
    def __init__(self):
        self.inputArray =  []
        self.outputArray = []

        #transforms stored per n frames
        self.frames = []

        self.extractedTransforms = []
        self.extractedPositions  = []

        self.manipulatedTransforms = []
        self.manipulatedPositions  = []

        self.predictedTransforms = []
        self.predictedPositions  = []

        self.recomposedTransforms = []
        self.recomposedTransforms  = []

        self.skipJoints = []

        self.modelJsonFile = ""
        self.modelWeightsFile = ""
        self.model = False
        self.dataMeanList = []
        self.dataStdevList = []

        self.lineSize = 2
        self.lineColor = [1.0,1.0,1.0]

        self.scaleOffset = 1.0
        self.rotateHeadDegrees = 0.0
        self.headTranslateY = 0.0

        self.oldPoseDiff = 0
        self.curPoseDiff = 0

        self.flip = False

    def setModelFiles(self,modelJsonFile,modelWeightsFile):
        self.modelJsonFile = modelJsonFile
        self.modelWeightsFile = modelWeightsFile               

    def updateModel(self):
        if self.modelJsonFile.isfile() and self.modelWeightsFile.isfile():
            print ("Loading model: %s and %s"%(self.modelJsonFile, self.modelWeightsFile))
            jsonFile = open(self.modelJsonFile,'r')
            jsonString = jsonFile.read().replace('\n', '')
            model = model_from_json(jsonString)
            model.load_weights(self.modelWeightsFile)
            jsonFile.close()
            jsonFile = open(self.modelJsonFile,'r')
            jsonNodes = json.loads(jsonFile.read())
            self.dataMeanList = jsonNodes['dataMeanList']
            self.dataStdevList = jsonNodes['dataStdevList']

        else:
            model =  False
        self.model = model

    def clearCache(self):
        """
        An instance of this class 'operation' will store self.frames worth
        of input data. When processing of extracted transforms 
        switches to a new Scene (animation clip), we need to start over to avoid
        discontinuity over the stored frames. This method gets called
        when operation is used to extract transform on a new Scene.
        """
        self.inputArray = []

    def vive2fbx(self,transformListRaw):

        transformList = copy.deepcopy(transformListRaw)
        hmdMx4 = transformList[0]
        rControllerMx4 = transformList[1]
        lControllerMx4 = transformList[2]

        #uniform scale
        hmdMx4[3:4,0:3] = hmdMx4[3:4,0:3]*self.scaleOffset
        rControllerMx4[3:4,0:3] = rControllerMx4[3:4,0:3]*self.scaleOffset
        lControllerMx4[3:4,0:3] = lControllerMx4[3:4,0:3]*self.scaleOffset       

        self.joints = joints('/home/daveotte/work/vr_avatar/rig/avatar.xml')

        #apply head local offset

        #get xml hmd joint, who's parent is the world
        hmdJoint = self.joints.getJoint('hmd')

        #place the xml hmd joint per vive telemetry
        hmdJoint.npMx = hmdMx4

        #get the headMx4, which is the local offset from hmdJoint.
        #now headMx4 is like an fbx headMx4
        headMx4 = self.joints.getJoint('head').GetNodeGlobalTransform()

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)
        #send head to origin (leave behind the pos information...)
        headMx4 = util.extractRot(headMx4)

        #RIGHT
        #apply rHand local offset
        rControllerJoint = self.joints.getJoint('rController')
        rControllerJoint.npMx = rControllerMx4
        rHandMx4 = self.joints.getJoint('rHand').GetNodeGlobalTransform()

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        #rHandPosV3 = rHandPosV3 * self.scaleOffset
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #LEFT
        #apply lHand local offset
        lControllerJoint = self.joints.getJoint('lController')
        lControllerJoint.npMx = lControllerMx4
        lHandMx4 = self.joints.getJoint('lHand').GetNodeGlobalTransform()       

        #send lHand to the origin with head offset (and scale...I'm bigger.)
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        #lHandPosV3 = lHandPosV3 * self.scaleOffset
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #we brought everything to the origin for easy scaling,
        #so now let's put it back:

        #put head back:
        headPosV3scaled = headPosV3
        #headPosV3scaled[1] = self.scaleHeightOffset * headPosV3[1]
        headMx4 = util.setPos(headMx4,headPosV3scaled)

        #rotateHeadClockwise
        headMx4 = util.rotateMxAboutAxis(headMx4,1,self.rotateHeadDegrees*-1)

        #lowerHead
        headMx4[3:4,1:2] = headMx4[3:4,1:2]+self.headTranslateY

        #put rHand back:
        rHandPosV3 = util.getPosArray(rHandMx4) + headPosV3scaled
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)

        #put lHand back:
        lHandPosV3 = util.getPosArray(lHandMx4) + headPosV3scaled
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)




        #pack it up and return it.
        transformList[0] = headMx4
        transformList[1] = rHandMx4
        transformList[2] = lHandMx4

        return transformList

    def runPrediction(self):
        #that [0] needs to happen, but may not work that way.
        #may need to put in variable first, and var[0]
        if not self.model:
            self.updateModel()

        inputData = util.normalizeData(np.array([self.inputArray]),self.dataMeanList,self.dataStdevList)
        self.updatePredicted(self.model.predict_on_batch(inputData)[0])

    def drawExtracted(self,transformScale):
        print ("Drawing Extracted--------------------------")
        util.drawMxs(self.extractedTransforms,transformScale)
        util.drawPoints(self.extractedPositions,9,util.color.magenta)

    def drawManipulated(self,transformScale):
        util.drawMxs(self.manipulatedTransforms,transformScale)
        util.drawPoints(self.manipulatedPositions,9,util.color.magenta)

    def drawPredicted(self,transformScale):
        self.runPrediction()  
        util.drawMxs(self.predictedTransforms,transformScale)  
        util.drawPoints(self.predictedPositions,9,util.color.magenta)
        #self.updateStatistics()

    def drawRecomposed(self,transformScale):
        self.runPrediction()
        self.updateRecompose()
        util.drawMxs(self.recomposedTransforms,transformScale)
        util.drawPoints(self.recomposedPositions,9,util.color.magenta)

    def updateStatistics(self):
        """
        Run a diff between the manipulated transforms and the
        predicted transforms, and then set attrs that store
        the current diff, and a running average.
        """
        self.posDiff = 0
        for i in range(len(self.predictedTransforms)):
            self.posDiff = self.posDiff + util.diffMxPos(self.predictedTransforms[i], self.manipulatedTransforms[i])
        self.oldPoseDiff = copy.deepcopy(self.curPoseDiff)
        self.curPoseDiff = self.posDiff/len(self.predictedTransforms)
        self.avgPosediff = (self.oldPoseDiff + self.curPoseDiff)/2
        print ("---")
        print ("currPoseDiff: " + str(self.curPoseDiff))
        print ("avgPosediff: " + str(self.avgPosediff))


###
# Do the same thing to N joints
class predictNPosRot(operation):
    def __init__(self):
        super(predictNPosRot, self).__init__()
        #joints not to draw in recompose skeleton
        self.skipJoints = ['rForeArm','rHand']
        self.timeBuffer = 6
    
        self.scaleOffset = 0.82
        self.scaleHeightOffset = 0.85
        self.rotateHeadDegrees = 25
        self.headTranslateY = -17

        self.curPrevHeadList = [[0.0,0.0,0.0],[0.0,0.0,0.0]]


        self.positionOnly = False

    def operate(self,transformList,mirror=False):
        """
                                ["head", "world"],
                                ["rHand", "world"],    
                                ["lHand", "world"],    
                                ["rForeArm", "world"],   
                                .... 
        """
        self.extractedTransforms = copy.deepcopy(transformList)

        if mirror:
            for i in range(len(transformList)):
                transformList[i] = util.flipMx(transformList[i])



        headMx4 = transformList.pop(0)
        rHandMx4 = transformList.pop(0)
        lHandMx4 = transformList.pop(0)

        self.transformCount = len(transformList)

        #get head position v3
        headPosV3 = util.getPosArray(headMx4)

        #send head to origin
        headMx4 = util.extractRot(headMx4)

        #send rHand to the origin with head offset
        rHandPosV3 = util.getPosArray(rHandMx4)
        rHandPosV3 = rHandPosV3 - headPosV3
        rHandMx4 = util.setPos(rHandMx4, rHandPosV3)
        
        #send lHand to the origin with head offset
        lHandPosV3 = util.getPosArray(lHandMx4)
        lHandPosV3 = lHandPosV3 - headPosV3
        lHandMx4 = util.setPos(lHandMx4, lHandPosV3)

        #send rForeArm to the origin with head offset
        for i in range(len(transformList)):
            V3 = util.getPosArray(transformList[i])
            V3 = V3 - headPosV3
            transformList[i] = util.setPos(transformList[i], V3)

        self.curPrevHeadList.pop(0)
        self.curPrevHeadList.append(headPosV3)
        velocity = self.curPrevHeadList[1]-self.curPrevHeadList[0]

        #length of array divided by one frame's worth of dimensions
        # 12 + 9 + 1 + 12 = 34 per frame 

        if self.positionOnly:
            self.currentInputArray = []
            self.currentInputArray = util.getPosArray(rHandMx4).tolist() \
                            + util.getRotArray(headMx4).tolist() \
                            + [headPosV3[1]]\
                            + velocity.tolist()\
                            + util.getPosArray(lHandMx4).tolist()
        else:
            self.currentInputArray = []
            self.currentInputArray = util.getTransformArray(rHandMx4,True).tolist() \
                            + util.getRotArray(headMx4).tolist() \
                            + [headPosV3[1]]\
                            + velocity.tolist()\
                            + util.getTransformArray(lHandMx4,True).tolist()            

        while len(self.inputArray)/len(self.currentInputArray) < self.timeBuffer:
            self.inputArray = self.inputArray + self.currentInputArray
        
        #lop off the first frame
        del self.inputArray[:len(self.currentInputArray)]

        #push on the current frame
        self.inputArray = self.inputArray + self.currentInputArray
        
        #and the things we are trying to predict
        self.outputArray = []     

        if self.positionOnly:
            for transform in transformList:
                self.outputArray = self.outputArray + util.getPosArray(transform).tolist() 
        else:
            for transform in transformList:
                self.outputArray = self.outputArray + util.getPosArray(transform).tolist() + util.getRotArray(transform).tolist()

        #for draw
        if not self.positionOnly:
            self.manipulatedTransforms = [rHandMx4,headMx4,lHandMx4] + transformList

        self.manipulatedPositions = []
        for transform in transformList:
            self.manipulatedPositions.append(util.getPosArray(transform))

        self.manipulatedPositions.append(velocity.tolist())

        # stuff for recompose
        self.headPosV3 = headPosV3
        #self.rForeArmPosV3 = rForeArmPosV3

        self.rHandMx4 = rHandMx4
        self.lHandMx4 = lHandMx4
        self.headMx4 = headMx4

        #return as python lists...apparently.
        return self.inputArray, self.outputArray

    def updatePredicted(self,predictedOutput):
        ''' 
        Format results of prediction into positions and transforms.
        These will be drawn.
        '''

        if self.positionOnly:
            posStart = 0
            posEnd = 3
            offset = 3
            self.predictedTransforms = []
            self.predictedPositions = []
            for i in range(self.transformCount):
                ###
                ### turn the huge output array into prediction transforms

                #pull out position from predicted output array
                self.predictedPositions.append(predictedOutput[posStart:posEnd])

                posStart += offset
                posEnd += offset
        else:

            posStart = 0
            posEnd = 3
            rotEnd = 12
            offset = 12
            self.predictedTransforms = []
            self.predictedPositions = []
            for i in range(self.transformCount):
                #print ("this is my index: %d"%(i)
                ###
                ### turn the huge output array into prediction transforms

                #pull out position from predicted output array
                self.predictedPositions.append(predictedOutput[posStart:posEnd])

                #manufacture a transform with the position
                transform = util.setPos(util.identity(),predictedOutput[posStart:posEnd])

                #pull out the rotation array, and complete the transform construction
                transform = util.setRot(transform,predictedOutput[posEnd:rotEnd])
                transform = util.orthonormalize(transform)
                self.predictedTransforms.append(transform)
                posStart += offset
                posEnd += offset
                rotEnd += offset

    def updateRecompose(self):
        '''Recompose self.predictedPositions and self.predictedTransforms.'''
        self.recomposedPositions  = []
 
        ### recomposed transforms should end up in same order for drawing later.

        #recomposed the manipulated xforms (not predicted) This is for vive, since we have offset to add.

        self.recomposedTransforms = []

        if not self.positionOnly:
            transforms = copy.copy(self.manipulatedTransforms)
            for transform in transforms[0:3]:
                self.recomposedTransforms.append(util.addPosToMx4(transform,self.headPosV3))



        #now lets recompose the predicted positions and transforms. (mark predictd with magenta dot)
        for pos in self.predictedPositions:
            #get the predicted pos to recompose
            position = copy.copy(pos)
        
            #recompose the position
            self.recomposedPositions.append(position+self.headPosV3)
        
        if self.positionOnly:
            self.recomposedPositions.append(util.getPosArray(self.headMx4)+self.headPosV3)
            self.recomposedPositions.append(util.getPosArray(self.rHandMx4)+self.headPosV3)
            self.recomposedPositions.append(util.getPosArray(self.lHandMx4)+self.headPosV3)

 
        if not self.positionOnly:       
            for i in range(len(self.predictedTransforms)):
                #get the predicted transform
                recomposedTransform = copy.copy(self.predictedTransforms[i])
                
                #keep the rotation, but offset with recomposed position
                self.recomposedTransforms.append(util.setPos(recomposedTransform,self.recomposedPositions[i])) 




    def drawRecomposed(self,transformScale):
        self.runPrediction()
        self.updateRecompose()


        if not self.positionOnly:
            util.drawMxs(self.recomposedTransforms,transformScale)
        util.drawPoints(self.recomposedPositions,9,util.color.magenta)

        '''
        0 ["rHand", "world"],    
        6 ["rForeArm", "world"],     
        5 ["rShldr", "world"],   
        4 ["neck", "world"],        
        1 ["head", "world"], 

        4 ["neck", "world"],        
        7 ["lShldr", "world"],    
        8 ["lForeArm", "world"]  
        2 ["lHand", "world"],    

        3 ["hip", "world"],  
        4 ["neck", "world"],       


        1   ["head", "world"],
        0   ["rHand", "world"],    
        2   ["lHand", "world"],    
        3   ["hip", "world"],  
        4   ["abdomen", "world"],         
        5   ["neck", "world"],       
        6   ["rShldr", "world"],    
        7   ["rForeArm", "world"],     
        8   ["lShldr", "world"],    
        9   ["lForeArm", "world"],    
        10  ["rFoot", "world"],    
        11  ["lFoot", "world"],    
        12  ["rShin", "world"],    
        13  ["lShin", "world"],    
        14  ["rThigh", "world"],    
        15  ["lThigh", "world"] 
----------------------------------------

        0   ["rHand", "world"],    
        7   ["rForeArm", "world"],     
        6   ["rShldr", "world"],    
        5   ["neck", "world"],       
        8   ["lShldr", "world"],    
        9   ["lForeArm", "world"],    
        2   ["lHand", "world"],    

        1   ["head", "world"],
        5   ["neck", "world"],       
        4   ["abdomen", "world"],         
        3   ["hip", "world"],  

        10  ["rFoot", "world"],    
        12  ["rShin", "world"],    
        14  ["rThigh", "world"],    
        3   ["hip", "world"],  
        15  ["lThigh", "world"] 
        13  ["lShin", "world"],    
        11  ["lFoot", "world"],    

        '''  
        util.drawLines([util.getPosArray(self.recomposedTransforms[0]), \
                        util.getPosArray(self.recomposedTransforms[7]), \
                        util.getPosArray(self.recomposedTransforms[6]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[8]), \
                        util.getPosArray(self.recomposedTransforms[9]), \
                        util.getPosArray(self.recomposedTransforms[2])], \
                        self.lineSize,self.lineColor)

        util.drawLines([util.getPosArray(self.recomposedTransforms[1]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[3])], \
                        self.lineSize,self.lineColor)

        util.drawLines([util.getPosArray(self.recomposedTransforms[10]), \
                        util.getPosArray(self.recomposedTransforms[12]), \
                        util.getPosArray(self.recomposedTransforms[14]), \
                        util.getPosArray(self.recomposedTransforms[3]), \
                        util.getPosArray(self.recomposedTransforms[15]), \
                        util.getPosArray(self.recomposedTransforms[13]), \
                        util.getPosArray(self.recomposedTransforms[11])], \
                        self.lineSize,self.lineColor)


'''

        util.drawLines([util.getPosArray(self.recomposedTransforms[0]), \
                        util.getPosArray(self.recomposedTransforms[6]), \
                        util.getPosArray(self.recomposedTransforms[5]), \
                        util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[1])], \
                        self.lineSize,self.lineColor)
        util.drawLines([util.getPosArray(self.recomposedTransforms[4]), \
                        util.getPosArray(self.recomposedTransforms[7]), \
                        util.getPosArray(self.recomposedTransforms[8]), \
                        util.getPosArray(self.recomposedTransforms[2])], \
                        self.lineSize,self.lineColor)


        util.drawLines([util.getPosArray(self.recomposedTransforms[3]), \
                        util.getPosArray(self.recomposedTransforms[4])], \
                        self.lineSize,self.lineColor)

'''


class predictNPos(predictNPosRot):
    def __init__(self):
        super(predictNPos, self).__init__()
        self.positionOnly = True

    def drawRecomposed(self,transformScale):
        self.runPrediction()
        self.updateRecompose()


        if not self.positionOnly:
            util.drawMxs(self.recomposedTransforms,transformScale)
        util.drawPoints(self.recomposedPositions,9,util.color.magenta)

        '''
        0 hip
        1 abdomen
        2 neck 
        3 rShldr
        4 rForeArm
        5 lShldr
        6 lForeArm
        7 rFoot
        8 lFoot
        9 rShin
        10 lShin
        11 rThigh
        12 lThigh
        13 head
        14 rHand
        15 lHand


        14   ["rHand", "world"],    
        4   ["rForeArm", "world"],     
        3   ["rShldr", "world"],    
        2   ["neck", "world"],       
        5   ["lShldr", "world"],    
        6   ["lForeArm", "world"],    
        15   ["lHand", "world"],    

        13   ["head", "world"],
        2   ["neck", "world"],       
        1   ["abdomen", "world"],         
        0   ["hip", "world"],  

        7   ["rFoot", "world"],    
        9   ["rShin", "world"],    
        11  ["rThigh", "world"],    
        0   ["hip", "world"],  
        12  ["lThigh", "world"] 
        10  ["lShin", "world"],    
        8   ["lFoot", "world"],    

        '''  
        util.drawLines([self.recomposedPositions[14],\
                        self.recomposedPositions[4],\
                        self.recomposedPositions[3],\
                        self.recomposedPositions[2],\
                        self.recomposedPositions[5],\
                        self.recomposedPositions[6],\
                        self.recomposedPositions[15]],\
                        self.lineSize,self.lineColor)

        util.drawLines([self.recomposedPositions[13],\
                        self.recomposedPositions[2],\
                        self.recomposedPositions[1],\
                        self.recomposedPositions[0]],\
                        self.lineSize,self.lineColor)

        util.drawLines([self.recomposedPositions[7],\
                        self.recomposedPositions[9],\
                        self.recomposedPositions[11],\
                        self.recomposedPositions[0],\
                        self.recomposedPositions[12],\
                        self.recomposedPositions[10],\
                        self.recomposedPositions[8]],\
                        self.lineSize,self.lineColor)


