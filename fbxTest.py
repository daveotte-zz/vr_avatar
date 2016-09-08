
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')

from keras.models import Sequential
from keras.layers import Dense, Activation
import site


#for i in (sys.path):
#	print i

#import DisplayGlobalSettings



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

def main():
    


    # Prepare the FBX SDK.
    lSdkManager, lScene = InitializeSdkObjects()
    # Load the scene.

    #print "dude" + sys.argv[1]
    #fbxFile = "~/work/mocap_animations/01/01_01.fbx"
    lResult = LoadScene(lSdkManager, lScene, "/home/daveotte/work/mocap_animations/01/01_02.fbx")
    print lResult



    # Destroy all objects created by the FBX SDK.
    lSdkManager.Destroy()
       
    sys.exit(0)


main()
