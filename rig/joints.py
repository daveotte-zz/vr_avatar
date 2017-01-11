import xml.etree.ElementTree as ET
import ast
import numpy as np
import lib.matrixUtil as mxUtil

class joints(object):
    def __init__(self,jointsXml):
    	tree = ET.parse(jointsXml)
    	root = tree.getroot()
        self.joints = []
        for child in root.iter('joint'):
        	self.joints.append(joint(child.attrib))

        self.setParents()
        self.setChildren()


    def getJoint(self,jointName):
        for j in self.joints:
            if j.name == jointName:
                return j       

    def printJoints(self):
        print str(len(self.joints))
        for j in self.joints:
            print j

    def setParents(self):
    	for joint in self.joints:
    		if joint.parent != 'world':
    			joint.jointParent = self.getJoint(joint.parent)

    def setChildren(self):
    	for joint in self.joints:
    		if joint.jointParent:
    			joint.jointParent.AddChild(joint)

class joint(object):
    def __init__(self,jointDict):
    	self.__dict__ = jointDict
        self.children = []
        self.npMx = np.matrix(np.array(list(ast.literal_eval(self.transform))).reshape(4,4))
        self.jointParent = False

    def GetName(self):
        return self.name

    def GetChildCount(self):
        return len(self.children)

    def GetChild(self,index):
        return self.children[index]

    def AddChild(self, childNode):
        self.children.append(childNode)

    def GetNodeGlobalTransform(self,time=0):
    	'''
    	npMx is a local matrix offset from the parent. This
    	means we recursively multiply matrices to derive the global
    	transform.
    	'''
    	if self.jointParent:
    		return self.npMx*self.jointParent.GetNodeGlobalTransform()
    	else:
    		#no parent, so local offset is same as world transform.
    		return self.npMx

    def GetNodeLocalTransform(self,time=0):
    	return self.npMx
