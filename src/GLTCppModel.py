from CppModel import Model

class GLTCppModel(Model):
    def __init__(self, basedir, dbModel):
        Model.__init__(self, basedir)
        self.dbModel = dbModel
        self.src = self.createModule('src')
        self.src_core = self.src.createModule('core')
        self.src_geology = self.src.createModule('geology')
        
        self.configureTypes()
        self.configureFieldTypes()
        self.configureCore()
        self.configureGeology()
    def configureTypes(self):
        self.tInt = self.createType('int')
        self.tDouble = self.createType('double')
        self.tQString = self.createType('QString', 'QtCore/qstring.h')
        self.tQTime = self.createType('QTime', 'QtCore/qdatetime.h')
        self.tQDate = self.createType('QDate', 'QtCore/qdatetime.h')
        self.tQDateTime = self.createType('QDateTime', 'QtCore/qdatetime.h')
    def configureFieldTypes(self):
        self.createFieldType(self.dbModel.primitiveType('integer'), self.type('int'))
        self.createFieldType(self.dbModel.primitiveType('numeric'), self.type('double'))
        self.createFieldType(self.dbModel.primitiveType('text'), self.type('QString'))
        self.createFieldType(self.dbModel.primitiveType('time'), self.type('QTime'))
        self.createFieldType(self.dbModel.primitiveType('date'), self.type('QDate'))
        self.createFieldType(self.dbModel.primitiveType('timestamp'), self.type('QDateTime'))
    def configureCore(self):
        self.cSIPrefix = self.configureSiPrefix(table=self.dbModel.schemaCore.table('si_prefixes'))
    def configureSiPrefix(self, table):
        c = self.src_core.createClass('SIPrefix', table)
        c.createField(table.column('id'), 'setId', 'id', 'hasId', ' > 0')
        c.createField(table.column('name'), 'setName', 'name', 'hasName', '.length() > 0')
        c.createField(table.column('code'), 'setCode', 'code', 'hasCode', '.length() > 0')
        c.createField(table.column('symbol'), 'setSymbol', 'symbol', 'hasSymbol', '.length() > 0')
        c.createField(table.column('factor'), 'setFactor', 'factor', 'hasFactor', ' != 0.0')
        c.createField(table.column('description'), 'setDescription', 'description', '.length() > 0')
        return c
    def configureGeology(self):
        self.cProfileType = self.configureProfileTypes(self.dbModel.schemaGeology.table('profile_types'))
    def configureProfileTypes(self, table):
        c = self.src_geology.createClass('ProfileType', table)
        c.createField(table.column('id'), 'setId', 'id', 'hasId', ' > 0')
        c.createField(table.column('name'), 'setName', 'name', 'hasName', '.length() > 0')
        c.createField(table.column('code'), 'setCode', 'code', 'hasCode', '.length() > 0')
        c.createField(table.column('description'), 'setDescription', 'description', 'hasDescription', '.length() > 0')
        return c