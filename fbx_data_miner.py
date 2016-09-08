"""

 Copyright (C) 2001 - 2010 Autodesk, Inc. and/or its licensors.
 All Rights Reserved.

 The coded instructions, statements, computer programs, and/or related material 
 (collectively the "Data") in these files contain unpublished information 
 proprietary to Autodesk, Inc. and/or its licensors, which is protected by 
 Canada and United States of America federal copyright law and by international 
 treaties. 
 
 The Data may not be disclosed or distributed to third parties, in whole or in
 part, without the prior written consent of Autodesk, Inc. ("Autodesk").

 THE DATA IS PROVIDED "AS IS" AND WITHOUT WARRANTY.
 ALL WARRANTIES ARE EXPRESSLY EXCLUDED AND DISCLAIMED. AUTODESK MAKES NO
 WARRANTY OF ANY KIND WITH RESPECT TO THE DATA, EXPRESS, IMPLIED OR ARISING
 BY CUSTOM OR TRADE USAGE, AND DISCLAIMS ANY IMPLIED WARRANTIES OF TITLE, 
 NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE OR USE. 
 WITHOUT LIMITING THE FOREGOING, AUTODESK DOES NOT WARRANT THAT THE OPERATION
 OF THE DATA WILL BE UNINTERRUPTED OR ERROR FREE. 
 
 IN NO EVENT SHALL AUTODESK, ITS AFFILIATES, PARENT COMPANIES, LICENSORS
 OR SUPPLIERS ("AUTODESK GROUP") BE LIABLE FOR ANY LOSSES, DAMAGES OR EXPENSES
 OF ANY KIND (INCLUDING WITHOUT LIMITATION PUNITIVE OR MULTIPLE DAMAGES OR OTHER
 SPECIAL, DIRECT, INDIRECT, EXEMPLARY, INCIDENTAL, LOSS OF PROFITS, REVENUE
 OR DATA, COST OF COVER OR CONSEQUENTIAL LOSSES OR DAMAGES OF ANY KIND),
 HOWEVER CAUSED, AND REGARDLESS OF THE THEORY OF LIABILITY, WHETHER DERIVED
 FROM CONTRACT, TORT (INCLUDING, BUT NOT LIMITED TO, NEGLIGENCE), OR OTHERWISE,
 ARISING OUT OF OR RELATING TO THE DATA OR ITS USE OR ANY OTHER PERFORMANCE,
 WHETHER OR NOT AUTODESK HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH LOSS
 OR DAMAGE. 
 
"""

import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/ImportScene')
sys.path.append('/usr/local/lib/python2.7/site-packages')
sys.path.append('/home/daveotte/work')
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

    
    #fbxFile = "~/work/mocap_animations/01/01_01.fbx"
    lResult = LoadScene(lSdkManager, lScene, "/home/daveotte/work/mocap_animations/01/01_02.fbx")
    print lResult



    # Destroy all objects created by the FBX SDK.
    lSdkManager.Destroy()
       
    sys.exit(0)


main()
