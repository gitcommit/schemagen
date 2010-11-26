from Model import Database, PrimitiveType, Schema, Sequence, Table, Column, DatabaseConstant, PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint

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
        
        self.seqTags = Sequence(self.schemaData, 'seq_tags')
        self.tTags = Table(self.schemaData, 'tags')
        self.tTags_id = Column(self.tTags, 'id', self.tInt, nullable=False, sequence=self.seqTags)
        self.tTags_parentId = Column(self.tTags, 'parent_id', self.tInt, nullable=True, defaultConstant=self.cNULL)
        self.tTags_name = Column(self.tTags, 'name', self.tText, nullable=False, defaultText='New Tag', preventEmptyText=True)
        self.tTags_position = Column(self.tTags, 'position', self.tText, nullable=False, defaultValue=1, preventZero=True)
        self.tTags_pk = PrimaryKeyConstraint(self.tTags, 'pk_tags', [self.tTags_id,])
        self.tTags_u = UniqueConstraint(self.tTags, 'u_tags_name', [self.tTags_parentId, self.tTags_name])
        ForeignKeyConstraint(self.tTags, 'fk_tags_parent_exists', [self.tTags_parentId],
                             self.tTags, [self.tTags_id])