import sys

from GLTModel import GLTModel
from GLTCppModel import GLTCppModel

if '__main__' == __name__:
    dbModel = GLTModel()
    cppModel = GLTCppModel('test/cpp', dbModel)
    cppModel.create()
    crebas = dbModel.create()
    crebas.extend(dbModel.tests())
    f = open('test/sql/crebas.sql', 'w')
    f.write('\n'.join(crebas))
    f.close()
    
    sys.exit(0)