import sys

from GLTModel import GLTModel
from GLTCppModel import GLTCppModel

def help():
    print("USAGE: specify 'crebas' to create sql, 'cpp' to create cpp code.")
    
if '__main__' == __name__:
    if not ('crebas' or 'cpp' in sys.argv):
        help()
        sys.exit(-1)
    dbModel = GLTModel()
    cppModel = GLTCppModel('/Users/jolo/data/cppworkspace/schemagen/test/cpp', dbModel)
    if 'cpp' in sys.argv:
        cppModel.create()
    if 'crebas' in sys.argv:
        f = open('/Users/jolo/data/cppworkspace/schemagen/test/sql/crebas.sql', 'w')
        f.write('\n'.join(dbModel.create()))
        f.write('-- Tests follow')
        f.write('\n'.join(dbModel.tests()))
        f.close()
    
    sys.exit(0)