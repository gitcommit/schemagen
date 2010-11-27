from GLTModel import GLTModel
from GLTCppModel import GLTCppModel

if '__main__' == __name__:
    dbModel = GLTModel()
    cppModel = GLTCppModel('/Users/jolo/data/cppworkspace/schemagen/test/cpp', dbModel)
    cppModel.create()
    crebas = dbModel.create()
    crebas.extend(dbModel.tests())
        
    #print('\n'.join(crebas))