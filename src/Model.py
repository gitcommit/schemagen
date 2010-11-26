class Component(object):
    def __init__(self, name):
        self.name = name
    def qualifiedName(self):
        return self.name.upper()
    def create(self):
        return ['-- Creation of {} not implemented.'.format(self.name),]        
    
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
class PreventZeroConstraint(CheckConstraint):
    def __init__(self, table, name, column):
        CheckConstraint.__init__(self, table, name, '0 != {}'.format(column.name.upper()))
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
class Column(InTableComponent):
    def __init__(self, table, name, primitiveType, nullable=True, 
                 sequence=None, defaultText=None, defaultValue=None, defaultConstant=None,
                 preventEmptyText=False, preventZero=False):
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
    def hasDefault(self):
        return self.default is not None
    def create(self):
        buf = '{n} {tn}'.format(n=self.name.upper(),
                                tn=self.type.qualifiedName())
        if not self.nullable:
            buf += ' NOT NULL'
        if self.hasDefault():
            buf += ' {0}'.format(self.default.create())
        return [buf,]
class Schema(InDatabaseComponent):
    def __init__(self, database, name):
        InDatabaseComponent.__init__(self, database, name)
        self.database.registerSchema(self)
        self.sequences = {}
        self.tables = {}
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
        ret = ['-- CREATE DATABASE {};'.format(self.name.upper())]
        for pt in self.primitiveTypes.values():
            ret.extend(pt.create())
        for schema in self.schemas.values():
            ret.extend(schema.create())
            for sequence in schema.sequences.values():
                ret.extend(sequence.create())
            for table in schema.tables.values():
                ret.extend(table.create())
                if table.hasPrimaryKey():
                    ret.extend(table.primaryKey.create())
                for uc in table.uniqueConstraints.values():
                    ret.extend(uc.create())
                for cc in table.checkConstraints.values():
                    ret.extend(cc.create())
        for schema in self.schemas.values():
            for table in schema.tables.values():
                for fk in table.foreignKeys.values():
                    ret.extend(fk.create())
        return ret