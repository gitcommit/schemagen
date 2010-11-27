class Component(object):
    def __init__(self, name):
        self.name = name
    def qualifiedName(self):
        return self.name.upper()
    def create(self):
        return ['-- Creation of type {} name {} not implemented.'.format(self.__class__.__name__.upper(), self.qualifiedName()),]        
    def debug(self, msg):
        print('SQL Generation: {}'.format(msg))
class InDatabaseComponent(Component):
    def __init__(self, database, name):
        Component.__init__(self, name)
        self.database = database
        
class PrimitiveType(InDatabaseComponent):
    def __init__(self, database, name):
        InDatabaseComponent.__init__(self, database, name)
        self.database.registerPrimitiveType(self)
    def create(self):
        return ['-- Primitive Type: {}'.format(self.name.upper())]
    
class DatabaseConstant(InDatabaseComponent):
    def __init__(self, database, name):
        InDatabaseComponent.__init__(self, database, name)
        self.database.registerDatabaseConstant(self)
    def create(self):
        return ['-- Database Constant: {}'.format(self.qualifiedName())]
    
class InSchemaComponent(Component):
    def __init__(self, schema, name):
        Component.__init__(self, name)
        self.schema = schema
    def qualifiedName(self):
        return '{}.{}'.format(self.schema.name.upper(), self.name.upper())
class Procedure(InSchemaComponent):
    def __init__(self, schema, name, returnTypeText=None):
        InSchemaComponent.__init__(self, schema, name)
        self.schema.registerProcedure(self)
        self.returnTypeText = returnTypeText
        self.declBuf = []
        self.paramBuf = []
        self.bodyBuf = []
    def addBodyRow(self, row):
        self.bodyBuf.append(row)
    def addParameter(self, typeString, name=None, coltype=None):
        type = typeString
        if coltype is not None:
            type = '{}%TYPE'.format(coltype.fullName().upper())
        if name is not None:
            self.paramBuf.append('{n} {ts}'.format(n=name.upper(), ts=type.upper()))
        else:
            self.paramBuf.append(typeString.upper())
    def addDeclaration(self, name, typeString=None, coltype=None, defaultValue=None, noDefault=False):
        tBuf = typeString
        defExpr = 'NULL'
        if coltype is not None:
            tBuf = '{}%TYPE'.format(coltype.fullName().upper())
        if defaultValue is not None:
            defExpr = '{}'.format(defaultValue)
        if noDefault:
            return self.declBuf.append('{n} {t};'.format(n=name.upper(), t=tBuf))
        else:
            self.declBuf.append('{n} {t} DEFAULT {defexpr};'.format(n=name.upper(), t=tBuf, defexpr=defExpr))
    def create(self):
        buf = []
        buf.append('CREATE OR REPLACE FUNCTION {qn} (\n\t{params}\n)'.format(qn=self.qualifiedName(), 
                                                                             params=',\n\t'.join(self.paramBuf)))
        buf.append('RETURNS {}'.format(self.returnTypeText))
        buf.append('AS')
        buf.append('$$')
        buf.append('DECLARE')
        buf.append('\t{}'.format('\n\t'.join(self.declBuf)))
        buf.append('BEGIN')
        buf.append('\t{}'.format('\n\t'.join(self.bodyBuf)))
        buf.append('END;')
        buf.append('$$ LANGUAGE PLPGSQL;')
        return ['\n'.join(buf)]
class TriggerProcedure(Procedure):
    def __init__(self, schema, name):
        Procedure.__init__(self, schema, name, returnTypeText='TRIGGER')
        self.schema.database.registerTrigger(self)
class CreateProcedure(Procedure):
    def __init__(self, schema, name, table, columns):
        Procedure.__init__(self, schema, name, returnTypeText='{}'.format(table.qualifiedName()))
        self.schema.registerProcedure(self)
        self.table = table
        self.idCol = self.table.primaryKey.firstColumn()
        self.colnames = []
        self.values = []
        i = 1
        self.table.createProcedure = self
        for c in columns:
            self.addParameter('{}%TYPE'.format(c.fullName()))
            self.colnames.append(c.name.upper())
            self.values.append('${}'.format(i))
            i += 1
        self.addDeclaration('new_id', '{}%TYPE'.format(self.table.primaryKey.firstColumn().fullName()))
        self.addDeclaration('ret', self.table.qualifiedName(), noDefault=True)
        self.addBodyRow('INSERT INTO {tbl}({cols}) VALUES ({values}) RETURNING {idCol} INTO NEW_ID;'.format(tbl=self.table.qualifiedName(),
                                                                                                            cols=', '.join(self.colnames),
                                                                                                            values=', '.join(self.values),
                                                                                                            idCol=self.idCol.name.upper()))
        self.addBodyRow('SELECT INTO RET * FROM {tbl} T WHERE T.{idCol} = NEW_ID;'.format(tbl=self.table.qualifiedName(),
                                                                                          idCol = self.idCol.name.upper()))
        self.addBodyRow('RETURN RET;')
class UpdateProcedure(Procedure):
    def __init__(self, schema, name, table, columns):
        Procedure.__init__(self, schema, name, returnTypeText='{}'.format(table.qualifiedName()))
        self.schema.registerProcedure(self)
        self.table = table
        self.idCol = self.table.primaryKey.firstColumn()
        self.kv = []
        i = 1
        self.table.updateProcedure = self
        for c in columns:
            self.addParameter('{}%TYPE'.format(c.fullName()))
            if i != 1:
                self.kv.append('{col}=${ival}'.format(col=c.name.upper(), 
                                                      ival=i))
            i += 1
        self.addDeclaration('ret', self.table.qualifiedName(), noDefault=True)
        self.addBodyRow('UPDATE {tbl} SET {kv} WHERE {idCol}=$1;'.format(tbl=self.table.qualifiedName(),
                                                                         kv=', '.join(self.kv),
                                                                         idCol=self.idCol.name.upper()))
        self.addBodyRow('SELECT INTO RET * FROM {tbl} T WHERE T.{idCol}=$1;'.format(tbl=self.table.qualifiedName(),
                                                                                      idCol = self.idCol.name.upper()))
        self.addBodyRow('RETURN RET;')
class DeleteProcedure(Procedure):
    def __init__(self, schema, name, table, columns):
        Procedure.__init__(self, schema, name, returnTypeText='{}%TYPE'.format(table.primaryKey.firstColumn().fullName().upper()))
        self.schema.registerProcedure(self)
        self.table = table
        self.idCol = self.table.primaryKey.firstColumn()
        self.kv = []
        self.table.deleteProcedure = self
        for c in columns:
            self.addParameter('{}%TYPE'.format(c.fullName()))
            
        self.addBodyRow('DELETE FROM {tbl} WHERE {idCol}=$1;'.format(tbl=self.table.qualifiedName(),
                                                                     idCol=self.idCol.name.upper()))
        self.addBodyRow('RETURN $1;')
class OrderStatement(object):
    def __init__(self, column, ascending=True):
        self.column = column
        self.ascending = ascending
    def sql(self):
        if self.ascending:
            return '{} ASC'.format(self.column.name.upper())
        return '{} DESC'.format(self.column.name.upper())
class GetAllProcedure(Procedure):
    def __init__(self, schema, name, table, orderStmts):
        Procedure.__init__(self, schema, name, returnTypeText='REFCURSOR')
        self.schema.registerProcedure(self)
        self.table = table
        self.idCol = self.table.primaryKey.firstColumn()
        self.colnames = []
        o = []
        for cn in self.table.columnSequence:
            self.colnames.append(self.table.column(cn).name.upper())
        self.table.getAllProcedure = self
        for ost in orderStmts:
            o.append(ost.sql())
        self.addParameter('REFCURSOR', 'CURS')
            
        self.addBodyRow('OPEN CURS FOR SELECT {cols} FROM {tbl} ORDER BY {o};'.format(cols=', '.join(self.colnames),
                                                                                     tbl=self.table.qualifiedName(),
                                                                                     o=', '.join(o)))
        self.addBodyRow('RETURN CURS;')
class Sequence(InSchemaComponent):
    def __init__(self, schema, name):
        InSchemaComponent.__init__(self, schema, name)
        self.schema.registerSequence(self)
    def create(self):
        return ['CREATE SEQUENCE {};'.format(self.qualifiedName())]
class Table(InSchemaComponent):
    def __init__(self, schema, name):
        InSchemaComponent.__init__(self, schema, name)
        self.schema.registerTable(self)
        self.columnSequence = []
        self.columns = {}
        self.uniqueConstraints = {}
        self.checkConstraints = {}
        self.foreignKeys = {}
        self.referencingForeignKeys = {}
        self.primaryKey = None
        self.auditTable = None
        self.auditTrigger = None
        self.createProcedure = None
        self.updateProcedure = None
        self.deleteProcedure = None
        self.getAllProcedure = None
    def createCreateProcedure(self, schema, name, columns):
        CreateProcedure(schema, name, self, columns)
    def createUpdateProcedure(self, schema, name, columns):
        UpdateProcedure(schema, name, self, columns)
    def createDeleteProcedure(self, schema, name, primaryKeyColumn):
        DeleteProcedure(schema, name, self, [primaryKeyColumn])
    def createGetAllProcedure(self, schema, name, orderStmts):
        GetAllProcedure(schema, name, self, orderStmts)
    def createAuditTable(self, auditSchema):
        self.auditTable = AuditTable(auditSchema, self)
        self.auditTrigger = Trigger(self, 'tr_audit_{}'.format(self.name), self.auditTable.triggerProcedure, before=False, 
                                    onInsert=True, onUpdate=True, onDelete=True)
        return self.auditTable
    def createColumn(self, name, primitiveType, nullable=True, 
                 sequence=None, defaultText=None, defaultValue=None, defaultConstant=None,
                 preventEmptyText=False, preventZero=False, referencedColumn=None, preventValue=None):
        c = Column(self, name, primitiveType, nullable, sequence, defaultText, defaultValue, defaultConstant,
                   preventEmptyText, preventZero, preventValue)
        if referencedColumn is not None:
            ForeignKeyConstraint(localTable=self, 
                                 name='fk_{tn}_{fkn}_exists'.format(tn=self.name.upper(), fkn=referencedColumn.name.upper()),
                                 localColumns=[c],
                                 referencedTable=c.table, referencedColumns=[referencedColumn])
        return c
    def createPrimaryKey(self, columns, name=None):
        n = name
        if n is None:
            n = 'pk_{}'.format(self.name)
        return PrimaryKeyConstraint(self, n, columns)
    def createUniqueConstraint(self, columns, name=None):
        n = name
        if n is None:
            cn = ['u_{}'.format(self.name.upper())]
            for c in columns:
                cn.append(c.name.upper())
            n = '_'.join(cn)
        return UniqueConstraint(self, n, columns)
    def registerForeignKey(self, c):
        self.foreignKeys[c.name] = c
    def foreignKey(self, name):
        return self.foreignKeys[name]
    def registerReferencingForeignKey(self, c):
        self.referencingForeignKeys[c.name] = c
    def referencingForeignKey(self, name):
        return self.referencingForeignKeys[name]
    def registerCheckConstraint(self, c):
        self.checkConstraints[c.name] = c
    def checkConstraint(self, name):
        return self.checkConstraints[name]
    def registerUniqueConstraint(self, c):
        self.uniqueConstraints[c.name] = c 
    def uniqueConstraint(self, name):
        return self.uniqueConstraints[name]
    def hasPrimaryKey(self):
        return self.primaryKey is not None
    def registerColumn(self, c):
        self.columnSequence.append(c.name)
        self.columns[c.name] = c 
    def column(self, name):
        return self.columns[name]
    def create(self):
        cdefs = []
        for n in self.columnSequence:
            cdefs.extend(self.column(n).create())
        return ['CREATE TABLE {tn}(\n\t{coldefs}\n);'.format(tn=self.qualifiedName(),
                                                             coldefs=',\n\t'.join(cdefs))]
class AuditTable(Table):
    def __init__(self, auditSchema, tableToAudit):
        Table.__init__(self, auditSchema, tableToAudit.name)
        self.tableToAudit = tableToAudit
        self.triggerProcedure = None
        self.auditedColumnNames = []
        for cn in tableToAudit.columnSequence:
            c = tableToAudit.column(cn)
            self.auditedColumnNames.append(c.name.upper())
            self.createColumn(c.name, c.type)
        
        self.createAuditColumns()
        self.createTriggerProcedure()
        
    def createTriggerProcedure(self):
        insertColumnNames = []
        updateColumnNames = []
        for n in self.auditedColumnNames:
            insertColumnNames.append('OLD.{}'.format(n))
            updateColumnNames.append('NEW.{}'.format(n))
        self.triggerProcedure = self.schema.createTriggerProcedure('audit_{}'.format(self.name))
        self.triggerProcedure.addDeclaration('NEW_VERSION', coltype=self.versionCol, defaultValue=1)
        self.triggerProcedure.addBodyRow("IF ('DELETE' = TG_OP OR 'UPDATE' = TG_OP) THEN")
        self.triggerProcedure.addBodyRow("\tSELECT INTO NEW_VERSION MAX({versCol}) + 1 FROM {auditT} T WHERE T.{pkCol}=OLD.{pkCol};".format(versCol=self.versionCol.name.upper(),
                                                                                                                                           auditT=self.qualifiedName(),
                                                                                                                                           pkCol=self.tableToAudit.primaryKey.firstColumn().name.upper()))

        self.triggerProcedure.addBodyRow("END IF;")
        self.triggerProcedure.addBodyRow("IF ('DELETE' = TG_OP) THEN")
        self.triggerProcedure.addBodyRow("\tINSERT INTO {auditT}({auditCols}, {versCol}, {opCol}) VALUES ({insertCols}, {vers}, TG_OP);".format(auditT=self.qualifiedName(),
                                                                                                                                               auditCols=', '.join(self.auditedColumnNames),
                                                                                                                                               versCol=self.versionCol.name.upper(),
                                                                                                                                               opCol=self.opCol.name.upper(),
                                                                                                                                               insertCols=', '.join(insertColumnNames),
                                                                                                                                               vers='NEW_VERSION'))
        self.triggerProcedure.addBodyRow('RETURN OLD;')
        self.triggerProcedure.addBodyRow("END IF;")
        
        self.triggerProcedure.addBodyRow("IF ('UPDATE' = TG_OP OR 'INSERT' = TG_OP) THEN")
        self.triggerProcedure.addBodyRow("\tINSERT INTO {auditT}({auditCols}, {versCol}, {opCol}) VALUES ({insertCols}, {vers}, TG_OP);".format(auditT=self.qualifiedName(),
                                                                                                                                               auditCols=', '.join(self.auditedColumnNames),
                                                                                                                                               versCol=self.versionCol.name.upper(),
                                                                                                                                               opCol=self.opCol.name.upper(),
                                                                                                                                               insertCols=', '.join(updateColumnNames),
                                                                                                                                               vers='NEW_VERSION'))
        
        self.triggerProcedure.addBodyRow("END IF;")
        self.triggerProcedure.addBodyRow("RETURN NULL; -- result is ignored since this is an AFTER trigger")
    def createAuditColumns(self):
        self.userCol = self.createColumn('db_user', 
                                         self.schema.database.primitiveType('text'), 
                                         nullable=False,
                                         defaultConstant=self.schema.database.databaseConstant('current_user'))
        self.tsCol = self.createColumn('ts',
                                       self.schema.database.primitiveType('timestamp'),
                                       nullable=False,
                                       defaultConstant=self.schema.database.databaseConstant('current_timestamp'))
        self.versionCol = self.createColumn('vers',
                                            self.schema.database.primitiveType('integer'),
                                            nullable=False,
                                            defaultValue=1)
        self.opCol = self.createColumn('op',
                                       self.schema.database.primitiveType('text'),
                                       nullable=False)
class InTableComponent(Component):
    def __init__(self, table, name):
        Component.__init__(self, name)
        self.table = table
class InColumnComponent(object):
    def __init__(self, column):
        object.__init__(self)
        self.column = column
class DefaultExpression(InColumnComponent):
    def __init__(self, column, expression):
        InColumnComponent.__init__(self, column)
        self.column.default = self
        self.expression = expression
    def create(self):
        return 'DEFAULT {}'.format(self.expression)
class SequenceDefaultExpression(DefaultExpression):
    def __init__(self, column, sequence):
        DefaultExpression.__init__(self, column, "NEXTVAL ('{}')".format(sequence.qualifiedName()))
        self.sequence = sequence
class TextDefaultExpression(DefaultExpression):
    def __init__(self, column, text):
        DefaultExpression.__init__(self, column, "'{}'".format(text))
        self.text = text
class NumericDefaultExpression(DefaultExpression):
    def __init__(self, column, value):
        DefaultExpression.__init__(self, column, '{}'.format(value))
        self.value = value
class DatabaseConstantDefaultExpression(DefaultExpression):
    def __init__(self, column, databaseConstant):
        DefaultExpression.__init__(self, column, databaseConstant.qualifiedName())
        self.databaseConstant = databaseConstant
class Constraint(InTableComponent):
    def __init__(self, table, name, type=None, columns=[]):
        InTableComponent.__init__(self, table, name)
        self.type = type
        self.columns = columns
    def firstColumn(self):
        if len(self.columns) != 1:
            return 'Constraint.firstColumn(): more or less than one column in constraint ',self.qualifiedName()
        return self.columns[0]
    def columnNames(self):
        buf = []
        for c in self.columns:
            buf.append(c.name.upper())
        return buf
    def create(self):
        return ['ALTER TABLE {tn} ADD CONSTRAINT {cn} {ct}({cols});'.format(tn=self.table.qualifiedName(),
                                                                            cn=self.name.upper(),
                                                                            ct=self.type,
                                                                            cols=', '.join(self.columnNames()))]
class PrimaryKeyConstraint(Constraint):
    def __init__(self, table, name, columns):
        Constraint.__init__(self, table, name, 'PRIMARY KEY', columns)
        self.table.primaryKey = self
class UniqueConstraint(Constraint):
    def __init__(self, table, name, columns):
        Constraint.__init__(self, table, name, 'UNIQUE', columns)
        self.table.registerUniqueConstraint(self)
class CheckConstraint(Constraint):
    def __init__(self, table, name, expression):
        Constraint.__init__(self, table, name)
        self.table.registerCheckConstraint(self)
        self.expression = expression
    def create(self):
        return ['ALTER TABLE {tn} ADD CONSTRAINT {cn} CHECK({chk});'.format(tn=self.table.qualifiedName(),
                                                                            cn=self.name.upper(),
                                                                            chk=self.expression)]
class PreventEmptyTextConstraint(CheckConstraint):
    def __init__(self, table, name, column):
        CheckConstraint.__init__(self, table, name, 'LENGTH({}) > 0'.format(column.name.upper()))
class PreventValueConstraint(CheckConstraint):
    def __init__(self, table, name, column, value):
        CheckConstraint.__init__(self, table, name, '{v} != {col}'.format(v=value,
                                                                          col=column.name.upper()))
class PreventZeroConstraint(PreventValueConstraint):
    def __init__(self, table, name, column):
        PreventValueConstraint.__init__(self, table, name, column, 0)
class ForeignKeyConstraint(InTableComponent):
    def __init__(self, localTable, name, localColumns, referencedTable, referencedColumns):
        InTableComponent.__init__(self, localTable, name)
        self.name = name
        self.localTable = self.table
        self.localColumns = localColumns
        self.referencedTable = referencedTable
        self.referencedColumns = referencedColumns
        self.localTable.registerForeignKey(self)
        self.referencedTable.registerReferencingForeignKey(self)
    def localColumnNames(self):
        ret = []
        for c in self.localColumns:
            ret.append(c.name.upper())
        return ret
    def referencedColumnNames(self):
        ret = []
        for c in self.referencedColumns:
            ret.append(c.name.upper())
        return ret
    def create(self):
        return ['ALTER TABLE {ltn} ADD CONSTRAINT {cn} FOREIGN KEY ({lcn}) REFERENCES {rtn}({rcn});'.format(ltn=self.localTable.qualifiedName(),
                                                                                                            cn=self.qualifiedName(),
                                                                                                            lcn=', '.join(self.localColumnNames()),
                                                                                                            rtn=self.referencedTable.qualifiedName(),
                                                                                                            rcn=', '.join(self.referencedColumnNames()))]
class Trigger(InTableComponent):
    def __init__(self, table, name, triggerProcedure, before=False, onInsert=True, onUpdate=True, onDelete=True):
        InTableComponent.__init__(self, table, name)
        self.table = table
        self.table.schema.database.registerTrigger(self)
        self.triggerProcedure = triggerProcedure
        self.table = table
        self.before = before
        self.onInsert = onInsert
        self.onUpdate = onUpdate
        self.onDelete = onDelete
    def create(self):
        befaft = 'NOT_DEFINED'
        act = []
        if self.before:
            befaft = 'BEFORE'
        if not self.before:
            befaft = 'AFTER'
        if self.onInsert:
            act.append('INSERT')
        if self.onUpdate:
            act.append('UPDATE')
        if self.onDelete:
            act.append('DELETE')
        return ['CREATE TRIGGER {tn} {beforeAfter} {actions} ON {tbl} FOR EACH ROW EXECUTE PROCEDURE {proc}();'.format(tn=self.name.upper(),
                                                                                                                       beforeAfter=befaft,
                                                                                                                       actions=' OR '.join(act),
                                                                                                                       tbl=self.table.qualifiedName(),
                                                                                                                       proc=self.triggerProcedure.qualifiedName())]
        
class Column(InTableComponent):
    def __init__(self, table, name, primitiveType, nullable=True, 
                 sequence=None, defaultText=None, defaultValue=None, defaultConstant=None,
                 preventEmptyText=False, preventZero=False, preventValue=None):
        InTableComponent.__init__(self, table, name)
        self.type = primitiveType
        self.nullable = nullable
        self.table.registerColumn(self)
        self.default = None
        if sequence is not None:
            self.default = SequenceDefaultExpression(self, sequence)
        if defaultValue is not None:
            self.default = NumericDefaultExpression(self, defaultValue)
        if defaultText is not None:
            self.default = TextDefaultExpression(self, defaultText)
        if defaultConstant is not None:
            self.default = DatabaseConstantDefaultExpression(self, defaultConstant)
        if preventEmptyText:
            PreventEmptyTextConstraint(self.table, 'chk_{}_not_empty'.format(self.name.upper()), self)
        if preventZero:
            PreventZeroConstraint(self.table, 'chk_{}_not_zero'.format(self.name.upper()), self)
        if preventValue is not None:
            PreventValueConstraint(self.table, 'chk_{}_not_illegal_value'.format(self.name.upper()), self, preventValue)
    def hasDefault(self):
        return self.default is not None
    def defaultExpression(self):
        if not self.hasDefault():
            return None
        return self.default.create()
    def create(self):
        buf = '{n} {tn}'.format(n=self.name.upper(),
                                tn=self.type.qualifiedName())
        if not self.nullable:
            buf += ' NOT NULL'
        if self.hasDefault():
            buf += ' {0}'.format(self.default.create())
        return [buf,]
    def fullName(self):
        return '{}.{}.{}'.format(self.table.schema.name, self.table.name, self.name)
class Schema(InDatabaseComponent):
    def __init__(self, database, name):
        InDatabaseComponent.__init__(self, database, name)
        self.database.registerSchema(self)
        self.sequences = {}
        self.tables = {}
        self.procedures = {}
    def createTable(self, name):
        return Table(self, name)
    def createSequence(self, name):
        return Sequence(self, name)
    def createProcedure(self, name):
        return Procedure(self, name)
    def createTriggerProcedure(self, name):
        return TriggerProcedure(self, name)
    def registerProcedure(self, p):
        self.procedures[p.name] = p 
    def procedure(self, name):
        return self.procedure[name]
    def registerTable(self, t):
        self.tables[t.name] = t
    def table(self, name):
        return self.tables[name]
    def registerSequence(self, s):
        self.sequences[s.name] = s 
    def sequence(self, name):
        return self.sequences[name]
    def create(self):
        return ['CREATE SCHEMA {};'.format(self.name.upper())]
class Database(Component):
    def __init__(self, name):
        Component.__init__(self, name)
        self.primitiveTypes = {}
        self.schemas = {}
        self.constants = {}
        self.triggers = {}
        self.createPrimitives()
        self.testQueries = []
    def addTest(self, sql):
        self.testQueries.append(sql)
    def tests(self):
        return self.testQueries
    def createPrimitives(self):
        self.tInt = PrimitiveType(self, 'integer')
        self.tNumeric = PrimitiveType(self, 'numeric')
        self.tText = PrimitiveType(self, 'text')
        self.tDate = PrimitiveType(self, 'date')
        self.tTime = PrimitiveType(self, 'time')
        self.tTimestamp = PrimitiveType(self, 'timestamp')
        
        self.cNULL = DatabaseConstant(self, 'null')
        self.cCurrentUser = DatabaseConstant(self, 'current_user')
        self.cCurrentTimestamp = DatabaseConstant(self, 'current_timestamp')
        
    def registerTrigger(self, t):
        self.triggers[t.name] = t
    def trigger(self, name):
        return self.triggers[name]
    def registerDatabaseConstant(self, c):
        self.constants[c.name] = c 
    def databaseConstant(self, name):
        return self.constants[name]
    def registerPrimitiveType(self, t):
        self.primitiveTypes[t.name] = t
    def primitiveType(self, name):
        return self.primitiveTypes[name]
    def registerSchema(self, s):
        self.schemas[s.name] = s 
    def schema(self, name):
        return self.schemas[name]
    def create(self):
        ret = ['ROLLBACK;',
               'BEGIN;',
               '-- CREATE DATABASE {};'.format(self.name.upper())]
        for pt in self.primitiveTypes.values():
            self.debug('declaring primitive type {}'.format(pt.qualifiedName()))
            ret.extend(pt.create())
        for schema in self.schemas.values():
            self.debug('creating schema {}'.format(schema.qualifiedName()))
            ret.extend(schema.create())
            for sequence in schema.sequences.values():
                self.debug('creating sequence {}'.format(sequence.qualifiedName()))
                ret.extend(sequence.create())
            for table in schema.tables.values():
                self.debug('creating table {}'.format(table.qualifiedName()))
                ret.extend(table.create())
                if table.hasPrimaryKey():
                    self.debug('creating primary key {}'.format(table.primaryKey.qualifiedName()))
                    ret.extend(table.primaryKey.create())
                for uc in table.uniqueConstraints.values():
                    self.debug('creating unique constraint {}'.format(uc.qualifiedName()))
                    ret.extend(uc.create())
                for cc in table.checkConstraints.values():
                    self.debug('creating check constraint {}'.format(cc.qualifiedName()))
                    ret.extend(cc.create())
        for schema in self.schemas.values():
            for table in schema.tables.values():
                for fk in table.foreignKeys.values():
                    self.debug('creating foreign key constraint {fk} on table {t}'.format(fk=fk.qualifiedName(), t=fk.table.qualifiedName()))
                    ret.extend(fk.create())
        for schema in self.schemas.values():
            for procedure in schema.procedures.values():
                self.debug('creating procedure {}'.format(procedure.qualifiedName()))
                ret.extend(procedure.create())
        for trigger in self.triggers.values():
            self.debug('creating trigger {}'.format(trigger.qualifiedName()))
            ret.extend(trigger.create())
        ret.extend(self.tests())
        return ret