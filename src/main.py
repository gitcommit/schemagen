from Test import Test

if '__main__' == __name__:
    t = Test()
    crebas = t.create()
    crebas.extend(t.tests())
        
    print('\n'.join(t.create()))