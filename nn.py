import sys
import os
import data




# Initialize the script plug-in
def initializeNN():

    try: 
        #I have a system to have different types of data groups, while reusing a bunch of code,
        #though right now I only have 1 type: fbxGroups
        #animManager = anim.animManager('animClips')
        #timeManager = anim.timeManager(animManager, actionManager)

        dataManager = data.dataManager('fbxGroups')
        nnManager = data.nnManager(dataManager)
        fbxNode = nnManager.fm.getObject(2)
        print fbxNode.searchDir

    except:
        sys.stderr.write( "Failed to initialize NN." )
        raise


initializeNN()