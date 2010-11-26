from Model import Database, PrimitiveType, Schema, Sequence, Table, DatabaseConstant,\
    OrderStatement

class Test(Database):
    def __init__(self):
        Database.__init__(self, 'db')
        self.tInt = PrimitiveType(self, 'integer')
        self.tNumeric = PrimitiveType(self, 'numeric')
        self.tText = PrimitiveType(self, 'text')
        self.tDate = PrimitiveType(self, 'date')
        self.tTime = PrimitiveType(self, 'time')
        self.tTimestamp = PrimitiveType(self, 'timestamp')
        
        self.cNULL = DatabaseConstant(self, 'null')
        self.cCurrentUser = DatabaseConstant(self, 'current_user')
        self.cCurrentTimestamp = DatabaseConstant(self, 'current_timestamp')
        
        self.schemaData = Schema(self, 'data')
        self.schemaAudit = Schema(self, 'audit')
        self.schemaLogic = Schema(self, 'logic')
        
        self.seqTags = Sequence(self.schemaData, 'seq_tags')
        self.tTags = Table(self.schemaData, 'tags')
        self.tTags_id = self.tTags.createColumn('id', self.tInt, nullable=False, sequence=self.seqTags)
        self.tTags_parentId = self.tTags.createColumn('parent_id', self.tInt, nullable=True, defaultConstant=self.cNULL, referencedColumn=self.tTags_id)
        self.tTags_name = self.tTags.createColumn('name', self.tText, nullable=False, defaultText='New Tag', preventEmptyText=True)
        self.tTags_description = self.tTags.createColumn('description', self.tText, nullable=False, defaultText='')
        self.tTags_position = self.tTags.createColumn('position', self.tInt, nullable=False, defaultValue=1, preventZero=True)
        self.tTags.createPrimaryKey([self.tTags_id,])
        self.tTags.createUniqueConstraint([self.tTags_parentId, self.tTags_name])
        self.tTags.createAuditTable(self.schemaAudit)
        self.tTags.createCreateProcedure(self.schemaLogic, 'create_tag', 
                                         [self.tTags_name, 
                                          self.tTags_description, 
                                          self.tTags_parentId,
                                          self.tTags_position])
        self.tTags.createUpdateProcedure(self.schemaLogic, 'update_tag',
                                         [self.tTags_id,
                                          self.tTags_name, 
                                          self.tTags_description, 
                                          self.tTags_parentId,
                                          self.tTags_position])
        self.tTags.createDeleteProcedure(self.schemaLogic, 'delete_tag', self.tTags_id)
        self.tTags.createGetAllProcedure(self.schemaLogic, 'get_all_tags', [OrderStatement(self.tTags_name, True)])
        