from GLTModel import GLTModel

if '__main__' == __name__:
    t = GLTModel()
    crebas = t.create()
    crebas.extend(t.tests())
        
    print('\n'.join(t.create()))