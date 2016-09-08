
import os
import data
from keras.models import Sequential
from keras.layers import Dense, Activation
import site


import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from DisplayGlobalSettings  import *
from DisplayHierarchy       import DisplayHierarchy
from DisplayMarker          import DisplayMarker
from DisplayMesh            import DisplayMesh
from DisplayUserProperties  import DisplayUserProperties
from DisplayPivotsAndLimits import DisplayPivotsAndLimits
from DisplaySkeleton        import DisplaySkeleton
from DisplayNurb            import DisplayNurb
from DisplayPatch           import DisplayPatch
from DisplayCamera          import DisplayCamera
from DisplayLight           import DisplayLight
from DisplayLodGroup        import DisplayLodGroup
from DisplayPose            import DisplayPose
from DisplayAnimation       import DisplayAnimation
from DisplayGenericInfo     import DisplayGenericInfo


from FbxCommon import *


def DisplayMetaData(pScene):
    sceneInfo = pScene.GetSceneInfo()
    if sceneInfo:
        print("\n\n--------------------\nMeta-Data\n--------------------\n")
        print("    Title: %s" % sceneInfo.mTitle.Buffer())
        print("    Subject: %s" % sceneInfo.mSubject.Buffer())
        print("    Author: %s" % sceneInfo.mAuthor.Buffer())
        print("    Keywords: %s" % sceneInfo.mKeywords.Buffer())
        print("    Revision: %s" % sceneInfo.mRevision.Buffer())
        print("    Comment: %s" % sceneInfo.mComment.Buffer())

        thumbnail = sceneInfo.GetSceneThumbnail()
        if thumbnail:
            print("    Thumbnail:")

            if thumbnail.GetDataFormat() == FbxThumbnail.eRGB_24 :
                print("        Format: RGB")
            elif thumbnail.GetDataFormat() == FbxThumbnail.eRGBA_32:
                print("        Format: RGBA")

            if thumbnail.GetSize() == FbxThumbnail.eNOT_SET:
                print("        Size: no dimensions specified (%ld bytes)", thumbnail.GetSizeInBytes())
            elif thumbnail.GetSize() == FbxThumbnail.e64x64:
                print("        Size: 64 x 64 pixels (%ld bytes)", thumbnail.GetSizeInBytes())
            elif thumbnail.GetSize() == FbxThumbnail.e128x128:
                print("        Size: 128 x 128 pixels (%ld bytes)", thumbnail.GetSizeInBytes())

def DisplayContent(pScene):
    lNode = pScene.GetRootNode()

    if lNode:
        for i in range(lNode.GetChildCount()):
            DisplayNodeContent(lNode.GetChild(i))

def DisplayNodeContent(pNode):
    if pNode.GetNodeAttribute() == None:
        print("NULL Node Attribute\n")
    else:
        lAttributeType = (pNode.GetNodeAttribute().GetAttributeType())

        if lAttributeType == FbxNodeAttribute.eMarker:
            DisplayMarker(pNode)
        elif lAttributeType == FbxNodeAttribute.eSkeleton:
            DisplaySkeleton(pNode)
        elif lAttributeType == FbxNodeAttribute.eMesh:
            DisplayMesh(pNode)
        elif lAttributeType == FbxNodeAttribute.eNurbs:
            DisplayNurb(pNode)
        elif lAttributeType == FbxNodeAttribute.ePatch:
            DisplayPatch(pNode)
        elif lAttributeType == FbxNodeAttribute.eCamera:
            DisplayCamera(pNode)
        elif lAttributeType == FbxNodeAttribute.eLight:
            DisplayLight(pNode)

    DisplayUserProperties(pNode)
    DisplayTarget(pNode)
    DisplayPivotsAndLimits(pNode)
    DisplayTransformPropagation(pNode)
    DisplayGeometricTransform(pNode)

    for i in range(pNode.GetChildCount()):
        DisplayNodeContent(pNode.GetChild(i))

def DisplayTarget(pNode):
    if pNode.GetTarget():
        DisplayString("    Target Name: ", pNode.GetTarget().GetName())

def DisplayTransformPropagation(pNode):
    print("    Transformation Propagation")
    
    # Rotation Space
    lRotationOrder = pNode.GetRotationOrder(FbxNode.eSourcePivot)

    print("        Rotation Space:",)

    if lRotationOrder == eEulerXYZ:
        print("Euler XYZ")
    elif lRotationOrder == eEulerXZY:
        print("Euler XZY")
    elif lRotationOrder == eEulerYZX:
        print("Euler YZX")
    elif lRotationOrder == eEulerYXZ:
        print("Euler YXZ")
    elif lRotationOrder == eEulerZXY:
        print("Euler ZXY")
    elif lRotationOrder == eEulerZYX:
        print("Euler ZYX")
    elif lRotationOrder == eSphericXYZ:
        print("Spheric XYZ")
    
    # Use the Rotation space only for the limits
    # (keep using eEULER_XYZ for the rest)
    if pNode.GetUseRotationSpaceForLimitOnly(FbxNode.eSourcePivot):
        print("        Use the Rotation Space for Limit specification only: Yes")
    else:
        print("        Use the Rotation Space for Limit specification only: No")


    # Inherit Type
    lInheritType = pNode.GetTransformationInheritType()

    print("        Transformation Inheritance:",)

    if lInheritType == FbxTransform.eInheritRrSs:
        print("RrSs")
    elif lInheritType == FbxTransform.eInheritRSrs:
        print("RSrs")
    elif lInheritType == FbxTransform.eInheritRrs:
        print("Rrs")


def DisplayGeometricTransform(pNode):
    print("    Geometric Transformations")

    # Translation
    lTmpVector = pNode.GetGeometricTranslation(FbxNode.eSourcePivot)
    print("        Translation: %f %f %f" % (lTmpVector[0], lTmpVector[1], lTmpVector[2]))

    # Rotation
    lTmpVector = pNode.GetGeometricRotation(FbxNode.eSourcePivot)
    print("        Rotation:    %f %f %f" % (lTmpVector[0], lTmpVector[1], lTmpVector[2]))

    # Scaling
    lTmpVector = pNode.GetGeometricScaling(FbxNode.eSourcePivot)
    print("        Scaling:     %f %f %f" % (lTmpVector[0], lTmpVector[1], lTmpVector[2]))




# Initialize the script plug-in
def initializeNN():


    #I have a system to have different types of data groups, while reusing a bunch of code,
    #though right now I only have 1 type: fbxGroups
    #animManager = anim.animManager('animClips')
    #timeManager = anim.timeManager(animManager, actionManager)

    fbxManager = data.fbxManager('fbxGroups')
    fbxObj = fbxManager.getObject(3)
    for f in fbxObj.getFbxFiles():
        pass

    # Prepare the FBX SDK.
    lSdkManager, lScene = InitializeSdkObjects()
    # Load the scene.

    
    
    lResult = LoadScene(lSdkManager, lScene, f)
    DisplayContent(lScene)



    # Destroy all objects created by the FBX SDK.
    lSdkManager.Destroy()
       
    sys.exit(0)




initializeNN()