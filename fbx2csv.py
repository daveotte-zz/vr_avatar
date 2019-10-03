from lib.data import *
from lib.engine import *
import os
import lib.util as util

'''
bring in stuff to make an nnConfig object, and then make it
bring in the Scene.py to make a Scene object(s)
bring in engine.py, instantiate an engine, and then extract stuff 
'''

'''

The dataManager extraction is really confusing. I'd rather go:

numpyArrayForNN = getEverything('sceneName(s)', )

'''

os.environ['JSON'] = '/home/daveotte/work/vr_avatar/lib/experiment.json'
jsonNodes           = json.loads(open(util.getJsonFile()).read())
scenes   			= sceneManager(jsonNodes['experimentGroupIndices']).scenes
nnConfigManager		= nnConfigDataManager(jsonNodes['nnConfigs'])
nnConfig			= nnConfigManager.getObject('predictEverything')
engineObj 			= engine(nnConfig, scenes)
engineObj.setData()

#engineObj.nnConfig.writeCsvFile = <path other than default created by nnConfig>


#write out a 13 Gb csv file.
engineObj.write()

