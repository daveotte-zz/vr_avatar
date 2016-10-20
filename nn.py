
import sys
import os
import data
#from keras.models import Sequential
#from keras.layers import Dense, Activation


# Initialize the script plug-in
def initializeNN():


    fbxManager = data.fbxManager('fbxGroups')
    nnDataConfigurations = data.nnDataConfigurations('nnDataConfigurations')
    nnDataObj = fbxManager.getNnDataObj(nnDataConfigurations.getObject('test'))
    nnDataObj.write('/home/daveotte/work/output.csv')
    #nnDataObj.printData()
    '''
    fbxObj = fbxManager.getObject(23)
    for f in fbxObj.getFbxFiles():
        print f
        pass

    # Prepare the FBX SDK.
    lSdkManager, lScene = InitializeSdkObjects()
    # Load the scene.
 
    
    lResult = LoadScene(lSdkManager, lScene, f)

    #SaveScene(pSdkManager, pScene, "./testBinaryExport.fbx", pFileFormat = -1, pEmbedMedia = False)
    

    for i in range(lScene.GetNodeCount()):
        print lScene.GetNode(i).GetName()

    # Destroy all objects created by the FBX SDK.
    lSdkManager.Destroy()
    '''  
    sys.exit(0)




initializeNN()