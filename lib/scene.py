
import sys

from lib.operations import *
from pathlib import Path
import ast

sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from FbxCommon import *
import numpy as np
from OpenGL.GL import *




class Scene:
    """Scene base class"""
    def __init__(self,fileName):
        self.fileName = fileName 
        self.needsInitializing = True 
        self.title = self.name = Path(self.fileName).stem
        self.type = "fbx"

    @property
    def startTime(self):
        self.initialize()
        return self.start

    @property
    def endTime(self):
        self.initialize()
        return self.end
 
    @property
    def jointRoot(self):
        self.initialize()
        return self.jointRootNode 

    def makeSkeletonNodeNameList(self):
        """
        Create list of joints in skeleton. Walk hierarchy
        from specified root node to make the list.
        """       
        self.skeletonNodeNameList = []
        self.walkHierarchy(self.jointRoot)

    def walkHierarchy(self, node):
        """
        Walk hierarchy to draw lines from parent to children.
        """
        self.skeletonNodeNameList.append(node.GetName())
        for i in range(node.GetChildCount()):
                self.walkHierarchy(node.GetChild(i))

    def drawSkeleton(self,frame,transformScale,drawTransforms=True,skipJointNames=[]):
        glColor3f(1.0,1.0,1.0);
        glLineWidth(1)
        glBegin(GL_LINE_STRIP)
        self.drawSkeletonLines(self.jointRoot,0,frame,skipJointNames)
        glEnd()
        if drawTransforms:
            self.drawSkeletonTransforms(frame,transformScale,skipJointNames)

    def drawSkeletonLines(self,pNode,pDepth,frame,skipJointNames=[]):
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
            childName = str(pNode.GetChild(i).GetName())
            if childName in skipJointNames:
                glEnd()
                glBegin(GL_LINE_STRIP)
            else:
                mx = self.getNpGlobalTransform(pNode.GetName(),frame)

                glVertex3fv(mx[3,0:3]) 
                mx = self.getNpGlobalTransform(pNode.GetChild(i).GetName(),frame)
                glVertex3fv(mx[3,0:3])  
            if pNode.GetChild(i).GetChildCount():
                self.drawSkeletonLines(pNode.GetChild(i), pDepth + 1,frame,skipJointNames)
            else:
                glEnd()
                glBegin(GL_LINE_STRIP)

    def drawSkeletonTransforms(self,frame,transformScale,skipJointNames=[]):
        for nodeName in self.skeletonNodeNameList:
            if nodeName not in skipJointNames:
                util.drawMx(self.getFbxNodeNpTransformAtFrame(nodeName,frame),transformScale)

    def getNodeIndexByName(self,jointName):
        self.initialize()
        return self.jointNameAndIndexDict[jointName]

class viveScene(Scene):
    """
    Library to work with recordered vive telemetry Scene (a .csv file).
    """
    def __init__(self, fileName):
        super(viveScene, self).__init__(fileName)
        self.type = "vive"

    def initialize(self):
        if self.needsInitializing:
            print ("Initializing vive Scene: %s"%(self.fileName))
            #load Scene into lScene?
            self.needsInitializing          = False
            self.fileLines = [line.rstrip('\r\n') for line in open(self.fileName)]
            npList = np.loadtxt(self.fileName,skiprows=1,delimiter=',')
            #first line of file has a dict representation of Scene info. Handy, right?
            self.configDict = ast.literal_eval(self.fileLines.pop(0))
            self.jointsObj  = nodes(self.configDict['jointRoot'], \
                                    self.configDict['joints'],\
                                    self.configDict['order'], npList)
            self.start                      = self.configDict['start']
            self.end                        = self.configDict['end']
            self.jointNameAndIndexDict      = self.getJointNameAndIndexDict()
            self.jointRootNode              = self.jointsObj.getJoint(self.configDict["jointRoot"])
            self.makeSkeletonNodeNameList()
 

    def getJoint(self,jointName):
        for j in self.joints:
            if j.name == jointName:
                return j

    def getJointNameAndIndexDict(self):
        """
        Create dictionary lookup table with joint name 
        as keys, and index number by value
        """
        self.initialize()
        indexDict = {}

        for joint in self.jointsObj.joints:
            indexDict[joint.name]=self.jointsObj.joints.index(joint)
        return indexDict

    def getFbxNodeNpTransformAtFrame(self, jointName, frame, transformSpace="world"):
        """
        Return numpy mx4 for a node within the fbx Scene at a specificed time.
        """
        if transformSpace=="world":
            return self.getGlobalTransform(jointName, frame)
        elif transformSpace=="local":
            print ("This doesn't work with local yet.")
        else:
            print ("Need to specify 'world' or 'local'.")


    def getNpGlobalTransform(self, jointName, time=0):
        return self.getGlobalTransform(jointName,time)

    #def getNpLocalTransform(self, jointName, time=0):
    #    return util.fbxMxtoNumpyMx(self.getLocalTransform(jointName,time))

    def getGlobalTransform(self, jointName, time=0):
        """
        Return transform of specificied joint node,
        at the specified time. The joint may not be there...
        return identity if not there.
        """
        self.initialize()
        node = self.jointsObj.getJoint(jointName)
        if node:
            return node.GetNodeGlobalTransform(time)
        else:
            return util.identity()     

    def destroy(self):
        if not self.needsInitializing:
            print ('Destroy: ' + self.title)
            #self.lSdkManager.Destroy()
        self.needsInitializing = True

class fbxScene(Scene):
    """
    Library to work with an fbx Scene (a .fbx file).
    """
    def __init__(self, fileName):
        super(fbxScene, self).__init__(fileName)

    def initialize(self):
        if self.needsInitializing:
            print ("Initializing: %s"%(self.fileName))
            self.time        = FbxTime()
            self.lSdkManager, self.lScene   = InitializeSdkObjects()
            lResult                         = LoadScene(self.lSdkManager, self.lScene, self.fileName)
            self.needsInitializing          = False
            
            lAnimStack                      = self.lScene.GetSrcObject(FbxCriteria.ObjectType(FbxAnimStack.ClassId), 0)
            
            #set fps to 24, even though these fbx files are at 30.
            #I'm doing this since Blender and Maya default to 24
            self.time.SetGlobalTimeMode(11)       
            lTs                             = lAnimStack.GetLocalTimeSpan()
            lStart                          = lTs.GetStart()
            lEnd                            = lTs.GetStop()
            lTmpStr                         = "something"
            self.start                      = int(str(lStart.GetTimeString(lTmpStr, 10).replace('*','')))
            self.end                        = int(str(lEnd.GetTimeString(lTmpStr, 10).replace('*','')))
            self.animEval                   = self.lScene.GetAnimationEvaluator()
            self.jointNameAndIndexDict      = self.getJointNameAndIndexDict()
            self.jointRootNode              = self.getNode('hip')
            self.makeSkeletonNodeNameList()

    def getJointNameAndIndexDict(self):
        """
        Create dictionary lookup table with joint name 
        as keys, and index number by value
        """
        self.initialize()
        indexDict = {}
        for i in range(self.lScene.GetNodeCount()):
            indexDict[self.lScene.GetNode(i).GetName()]=i
        return indexDict

    def getFbxNodeNpTransformAtFrame(self, jointName, frame, transformSpace="world"):
        """
        Return numpy mx4 for a node within the fbx Scene at a specificed time.
        """
        if transformSpace=="world":
            return util.fbxMxtoNumpyMx(self.getGlobalTransform(jointName, frame))
        elif transformSpace=="local":
            return util.fbxMxtoNumpyMx(self.getLocalTransform(jointName, frame))
        else:
            print ("Need to specify 'world' or 'local'.")

    def getNodeIndexByName(self,jointName):
        self.initialize()
        return self.jointNameAndIndexDict[jointName]

    def getNode(self,jointName):
        """
        Return FbxNode by joint name.
        """
        self.initialize()
        return self.lScene.GetNode(self.getNodeIndexByName(jointName))

    def getNpGlobalTransform(self, jointName, time=0):
        return util.fbxMxtoNumpyMx(self.getGlobalTransform(jointName,time))

    def getNpLocalTransform(self, jointName, time=0):
        return util.fbxMxtoNumpyMx(self.getLocalTransform(jointName,time))

    def getGlobalTransform(self, jointName, time=0):
        """
        Return transform of specificied joint node,
        at the specified time.
        """
        self.initialize()
        self.time.SetFrame(time)
        return self.animEval.GetNodeGlobalTransform(self.getNode(jointName),self.time)
 
    def getLocalTransform(self, jointName, time=0):
        self.initialize()
        self.time.SetFrame(time)
        return self.animEval.GetNodeLocalTransform(self.getNode(jointName),self.time)

    def destroy(self):
        if not self.needsInitializing:
            print ('Destroy: ' + self.title)
            self.lSdkManager.Destroy()
        self.needsInitializing = True
