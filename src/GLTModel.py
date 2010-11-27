from Model import Database, Schema, OrderStatement

class GLTModel(Database):
    def __init__(self):
        Database.__init__(self, 'db')
        
        self.schemaCore = Schema(self, 'core')
        self.schemaGeology = Schema(self, 'geology')
        self.schemaAudit = Schema(self, 'audit')
        self.schemaLogic = Schema(self, 'logic')
        
        self.createCore()
        self.createGeology()
        self.setupTests()
    def createGeology(self):
        self.tRockClasses = self.createStandardHierarchicalTable(self.schemaGeology, 'rock_classes', 
                                                                 createProcedureName='create_rock_class', 
                                                                 updateProcedureName='update_rock_class', 
                                                                 deleteProcedureName='delete_rock_class', 
                                                                 getAllProcedureName='get_all_rock_classes')
    def createStandardHierarchicalTable(self, schema, name,
                                        createProcedureName,
                                        updateProcedureName,
                                        deleteProcedureName,
                                        getAllProcedureName):
        t = schema.createTable(name)
        id = t.createColumn('id', self.tInt, nullable=False, sequence=schema.createSequence('seq_{}'.format(name)))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True, referencedColumn=id)
        name = t.createColumn('name', self.tText, nullable=False, defaultText='New Entry', preventEmptyText=True)
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name, parent_id])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, createProcedureName, [name, code, parent_id, description])
        t.createUpdateProcedure(self.schemaLogic, updateProcedureName, [id, name, code, parent_id, description])
        t.createDeleteProcedure(self.schemaLogic, deleteProcedureName, id)
        t.createGetAllProcedure(self.schemaLogic, getAllProcedureName, [OrderStatement(name, True)])
        return t
    def createRockClasses(self):
        self.tRockClasses()
    def createCore(self):
        self.createTags()
        self.createSiPrefixes()
        self.createUnits()
        self.createConstants()
    def createTags(self):
        self.tTags = self.schemaCore.createTable('tags')
        id = self.tTags.createColumn('id', self.tInt, nullable=False, 
                                     sequence=self.schemaCore.createSequence('seq_tags'))
        name = self.tTags.createColumn('name', self.tText, nullable=False, defaultText='New Tag', preventEmptyText=True)
        description = self.tTags.createColumn('description', self.tText, nullable=False, defaultText='')
        self.tTags.createPrimaryKey([id,])
        self.tTags.createUniqueConstraint([name])
        self.tTags.createAuditTable(self.schemaAudit)
        self.tTags.createCreateProcedure(self.schemaLogic, 'create_tag', [name, description])
        self.tTags.createUpdateProcedure(self.schemaLogic, 'update_tag', [id, name, description])
        self.tTags.createDeleteProcedure(self.schemaLogic, 'delete_tag', id)
        self.tTags.createGetAllProcedure(self.schemaLogic, 'get_all_tags', [OrderStatement(name, True)])
    def createSiPrefixes(self):
        self.tSiPrefixes = self.schemaCore.createTable('si_prefixes')
        id = self.tSiPrefixes.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_si_prefixes'))
        name = self.tSiPrefixes.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New SI Prefix')
        symbol = self.tSiPrefixes.createColumn('symbol', self.tText, nullable=False, preventEmptyText=True, defaultText='')
        code = self.tSiPrefixes.createColumn('code', self.tText, nullable=True)
        description = self.tSiPrefixes.createColumn('description', self.tText, nullable=False, defaultText='')
        factor = self.tSiPrefixes.createColumn('factor', self.tNumeric, nullable=False, preventValue=0.0)
        self.tSiPrefixes.createPrimaryKey([id])
        self.tSiPrefixes.createUniqueConstraint([name])
        self.tSiPrefixes.createUniqueConstraint([symbol])
        self.tSiPrefixes.createUniqueConstraint([code])
        self.tSiPrefixes.createUniqueConstraint([factor])
        self.tSiPrefixes.createAuditTable(self.schemaAudit)
        self.tTags.createCreateProcedure(self.schemaLogic, 'create_si_prefix', [name, code, symbol, factor, description])
        self.tTags.createUpdateProcedure(self.schemaLogic, 'update_si_prefix', [id, name, code, symbol, factor, description])
        self.tTags.createDeleteProcedure(self.schemaLogic, 'delete_si_prefix', id)
        self.tTags.createGetAllProcedure(self.schemaLogic, 'get_all_si_prefixes', [OrderStatement(name, True)])
    def createUnits(self):
        self.tUnits = self.schemaCore.createTable('units')
        id = self.tUnits.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_units'))
        base_unit_id = self.tUnits.createColumn('base_unit_id', self.tInt, nullable=True, referencedColumn=id)
        name = self.tUnits.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Unit')
        code = self.tUnits.createColumn('code', self.tText, nullable=True)
        symbol = self.tUnits.createColumn('symbol', self.tText, nullable=False, defaultText='Symbol')
        prefix_id = self.tUnits.createColumn('si_prefix_id', self.tInt, nullable=True, referencedColumn=self.tSiPrefixes.primaryKey.firstColumn())
        description = self.tUnits.createColumn('description', self.tText, nullable=False, defaultText='')
        self.tUnits.createPrimaryKey([id])
        self.tUnits.createUniqueConstraint([name])
        self.tUnits.createUniqueConstraint([symbol])
        self.tUnits.createUniqueConstraint([code])
        self.tUnits.createAuditTable(self.schemaAudit)
        self.tUnits.createCreateProcedure(self.schemaLogic, 'create_unit', [name, code, symbol, base_unit_id, prefix_id, description])
        self.tUnits.createUpdateProcedure(self.schemaLogic, 'update_unit', [id, name, code, symbol, base_unit_id, prefix_id, description])
        self.tUnits.createDeleteProcedure(self.schemaLogic, 'delete_unit', id)
        self.tUnits.createGetAllProcedure(self.schemaLogic, 'get_all_si_prefixes', [OrderStatement(name, True)])
    def createConstants(self):
        self.tConstants = self.schemaCore.createTable('constants')
        id = self.tConstants.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_constants'))
        name = self.tConstants.createColumn('name', self.tText, nullable=False, defaultText='New Constant', preventEmptyText=True)
        code = self.tConstants.createColumn('code', self.tText, nullable=True)
        symbol = self.tConstants.createColumn('symbol', self.tText, nullable=True)
        unit_id = self.tConstants.createColumn('unit_id', self.tInt, nullable=True, referencedColumn=self.tUnits.primaryKey.firstColumn())
        value = self.tConstants.createColumn('numeric_value', self.tNumeric, nullable=False, preventValue=0)
        self.tConstants.createPrimaryKey([id])
        self.tConstants.createUniqueConstraint([name])
        self.tConstants.createUniqueConstraint([code])
        self.tConstants.createUniqueConstraint([symbol])
        self.tConstants.createAuditTable(self.schemaAudit)
        self.tConstants.createCreateProcedure(self.schemaLogic, 'create_constant', [name, code, symbol, value, unit_id])
        self.tConstants.createUpdateProcedure(self.schemaLogic, 'update_constant', [id, name, code, symbol, value, unit_id])
        self.tConstants.createDeleteProcedure(self.schemaLogic, 'delete_constant', id)
        self.tConstants.createGetAllProcedure(self.schemaLogic, 'get_all_constants', [OrderStatement(name, True)])
    def setupTests(self):
        self.addTest("SELECT * FROM LOGIC.CREATE_TAG('foo', 'bar');")
        self.addTest("SELECT * FROM LOGIC.UPDATE_TAG(1, 'foobar', 'barfo');")
        self.addTest("SELECT * FROM LOGIC.DELETE_TAG(1);")
        self.addTest("SELECT LOGIC.GET_ALL_TAGS('all_tags');")
        self.addTest("FETCH ALL IN ALL_TAGS;")
        self.addTest("CLOSE ALL_TAGS;")