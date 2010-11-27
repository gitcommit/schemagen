import sys
import settings

from GLTModel import GLTModel
from GLTCppModel import GLTCppModel

def help():
    print("USAGE: specify 'crebas' to create sql, 'cpp' to create cpp code.")

def debug(msg):
    print('MESSAGE: {}'.format(msg))    
if '__main__' == __name__:
    if not ('crebas' or 'cpp' in sys.argv):
        help()
        sys.exit(-1)
    debug('Creating database model...')
    dbModel = GLTModel()
    debug('Database model created.')
    debug('Creating C++ model...')
    cppModel = GLTCppModel('{testDir}/cpp'.format(testDir=settings.testDir), dbModel)
    debug('C++ model created.')
    debug('Ready to generate code.')
    if 'cpp' in sys.argv:
        debug('Creating C++ code...')
        cppModel.create()
        debug('C++ code created.')
    if 'crebas' in sys.argv:
        debug('Creating SQL code...')
        f = open('{testDir}/sql/crebas.sql'.format(testDir=settings.testDir), 'w')
        f.write('\n'.join(dbModel.create()))
        f.write('-- Tests follow')
        f.write('\n'.join(dbModel.tests()))
        f.close()
        debug('SQL Code created.')
    debug('All jobs done. Exiting.')
    sys.exit(0)