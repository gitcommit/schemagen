import sys
import os

class Element(object):
	def __init__(self):
		object.__init__(self) 
	def create(self):
		raise RuntimeError('Creation of objects of type <{}> not implemented. aborting.'.format(self.__class__.__name__))
		sys.exit()
class CppType(Element):
	def __init__(self, model, name, includeFile):
		Element.__init__(self)
		self.model = model
		self.name = name
		self.includeFile = includeFile
		self.model.registerType(self)
class FieldType(Element):
	def __init__(self, databaseType, cppType):
		Element.__init__(self)
		self.databaseType = databaseType
		self.cppType = cppType
class Class(Element):
	def __init__(self, model, module, name, table=None):
		Element.__init__(self)
		self.model = model
		self.module = module
		self.name = name
		self.module.registerClass(self)
		self.table = table
	def create(self):
		path = self.module.fullPath()
		self.createHeader(path)
		self.createImplementation(path)
	def ctorDeclaration(self):
		return '{cn}({vars});'.format(cn=self.name, vars=', '.join(self.ctorArguments()))
	def dtorDeclaration(self):
		return 'virtual ~{cn}();'.format(cn=self.name)
	def hasTable(self):
		return self.table is not None
	def ctorArguments(self):
		if not self.hasTable():
			raise RuntimeError('{cn}: table is not set'.format(cn=self.__class__.__name__))
		ret = []
		for colName in self.table.columnSequence:
			col = self.table.column(colName)
			ret.append('const {cppType}& {coln}'.format(cppType=self.cppTypeFromDbCol(col).name, 
														coln=self.createMethodParamName(col)))
		return ret
	def varInitList(self):
		if not self.hasTable():
			raise RuntimeError('{cn}: table is not set'.format(cn=self.__class__.__name__))
		ret = []
		for colName in self.table.columnSequence:
			col = self.table.column(colName)
			ret.append('{var}({param})'.format(var=self.createLocalVarName(col), param=self.createMethodParamName(col)))
		return ret
	def cppTypeFromDbCol(self, dbCol):
		return self.model.fieldTypeFromDbType(dbCol.type).cppType
	def createMethodParamName(self, dbCol):
		return dbCol.name
	def createLocalVarName(self, dbCol):
		return '{coln}_'.format(coln=dbCol.name)
	def dataVariableDeclarations(self):
		if not self.hasTable():
			raise RuntimeError('{cn}: table is not set'.format(cn=self.__class__.__name__))
		ret = []
		for colName in self.table.columnSequence:
			col = self.table.column(colName)
			ret.append('{cppType} {varName};'.format(cppType=self.cppTypeFromDbCol(col).name,
													varName=self.createLocalVarName(self.table.column(colName))))
		return ret
	def createHeader(self, path):
		buf = ['// automatially generated class declaration for class {}'.format(self.name),
				'#include <orm/Entity.h>',
				'',
				'class {cn}: public Entity {{'.format(cn=self.name),
				'public:',
				'\t{}'.format(self.ctorDeclaration()),
				'\t{}'.format(self.dtorDeclaration()),
				'protected:',
				'private:',
				'\t{}'.format('\n\t'.join(self.dataVariableDeclarations())),
				'};',
				'']
		self.writeToFile('{p}/{n}.h'.format(p=path, n=self.name), buf)
	def createImplementation(self, path):
		buf = ['// automatially generated class implementation for class {}'.format(self.name),
				'',
				'#include <{cn}.h>'.format(cn=self.name),
				'',
				self.ctorImplementation(),
				'',
				self.dtorImplementation(),
				'']
		self.writeToFile('{p}/{n}.cpp'.format(p=path, n=self.name), buf)
	def writeToFile(self, fn, buf):
		f = open(fn, 'w')
		f.write('\n'.join(buf))
		f.write('\n')
		f.close()
	def ctorImplementation(self):
		ret = ['{cn}::{cn}({vars}):'.format(cn=self.name, vars=', '.join(self.ctorArguments())),
				'\tEntity()',
				'\t{}'.format(',\n\t'.join(self.varInitList())),
				'{ }']
		return '\n'.join(ret)
	def dtorImplementation(self):
		ret = ['{cn}::~{cn}() {{ }}'.format(cn=self.name)]
		return '\n'.join(ret)
	
class Module(Element):
	def __init__(self, model=None, module=None, name=None):
		Element.__init__(self)
		self.model = model
		self.module = module
		self.name = name
		self.modules = {}
		self.classes = {}
		self.schema = None
		if self.hasModel():
			self.model.registerModule(self)
		if self.hasModule():
			self.module.registerModule(self)
	def __str__(self):
		return self.name
	def registerClass(self, c):
		self.classes[c.name] = c
	def createClass(self, name, table):
		return Class(module=self, name=name, table=table, model=self.model)
	def hasModel(self):
		return self.model is not None
	def hasModule(self):
		return self.module is not None
	def registerModule(self, m):
		self.modules[m.name] = m
	def createModule(self, name):
		return Module(module=self, model=self.model, name=name)
	def pathBelowBasedir(self):
		buf = []
		buf.append(self.name)
		p = self.module
		while p is not None:
			buf.append(p.name)
			p = p.module
		buf.reverse()
		return '/'.join(buf)
	def fullPath(self):
		return '{}/{}'.format(self.model.basedir, self.pathBelowBasedir())
	def create(self):
		pwd = self.fullPath()
		if not os.path.exists(pwd):
			os.mkdir(pwd)
		for c in self.classes.values():
			c.create()
class Model(Element):
	def __init__(self, basedir):
		self.basedir = basedir
		self.modules = {}
		self.types = {}
		self.fieldTypes = []
		self.dbModel = None
	def registerType(self, t):
		self.types[t.name] = t
	def type(self, name):
		return self.types[name]
	def createType(self, name, includeFile=None):
		return CppType(self, name, includeFile)
	def createFieldType(self, dbType, cppType):
		t = FieldType(dbType, cppType)
		self.fieldTypes.append(t)
		return t
	def fieldTypeFromDbType(self, dbType):
		for t in self.fieldTypes:
			if dbType==t.databaseType:
				return t
		return None
	def registerModule(self, m):
		self.modules[m.name] = m
	def createModule(self, name):
		return Module(model=self, name=name)
	def setDbModel(self, dbModel):
		self.dbModel = dbModel
	def __str__(self):
		return self.basedir
	def create(self):
		if not os.path.exists(self.basedir):
			raise RuntimeError('Path <{}> does not exist. Create it before running this code generator.'.format(self.basedir))
		if not os.path.isdir(self.basedir):
			raise RuntimeError('Path <{}> is not a directory.'.format(self.basedir))
		for module in self.modules.values():
			print('processing: {}'.format(module.pathBelowBasedir()))
			module.create()