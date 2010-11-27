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
class Field(Element):
	def __init__(self, model, module, class_, dbCol, setterName, getterName, isSetName=None, isSetTest=None):
		Element.__init__(self)
		self.model = model
		self.module = module
		self.class_ = class_
		self.dbCol = dbCol
		self.setterName = setterName
		self.getterName = getterName
		self.isSetName = isSetName
		self.isSetTest = isSetTest
	def hasGetter(self):
		return len(self.getterName) > 0
	def hasSetter(self):
		return len(self.setterName) > 0
	def hasIsSetTest(self):
		if self.isSetName is None or self.isSetTest is None:
			return False
		return len(self.isSetName) > 0
	def cppType(self):
		return self.model.cppTypeFromDbCol(self.dbCol)
	def methodParamName(self):
		return self.dbCol.name
	def paramDecl(self):
		return 'const {cppType}& {coln}'.format(cppType=self.cppType().name, coln=self.methodParamName())
	def localVarName(self):
		return '{coln}_'.format(coln=self.dbCol.name)
	def varDecl(self):
		return '{cppType} {varName};'.format(cppType=self.cppType().name, varName=self.localVarName())
	def varInit(self):
		return '{var}({param})'.format(var=self.localVarName(), param=self.methodParamName())
	def isSetDecl(self):
		return 'virtual bool {cn}::{fn}() const;'.format(cn=self.class_.name, fn=self.isSetName)
	def isSetImpl(self):
		ret = ['bool {cn}::{fn}() const {{'.format(cn=self.class_.name,
														fn=self.isSetName),
				'\t return ({getter}{exp});'.format(getter=self.getterName, exp=self.isSetTest),
				'}']
		return '\n'.join(ret)
	def setterDecl(self):
		return 'virtual void {sn}({pdecl}) const;'.format(cppType=self.cppType().name,
														sn=self.setterName, 
														pdecl=self.paramDecl())
	def setterImpl(self):
		ret = ['void {cln}::{sn}({pdecl}) {{'.format(cln=self.class_.name,
													sn=self.setterName,
													pdecl=self.paramDecl()),
				'\t{var} = {parmn};'.format(var=self.localVarName(),
										parmn=self.methodParamName()),
				'}']
		return '\n'.join(ret)
	def getterDecl(self):
		return 'virtual {cppType} {gn}() const;'.format(cppType=self.cppType().name, gn=self.getterName)
	def getterImpl(self):
		ret = ['{cppType} {cn}::{gn}() const {{'.format(cppType=self.cppType().name,
													cn=self.class_.name,
													gn=self.getterName),
				'\treturn {var};'.format(var=self.localVarName()),
				'}']
		return '\n'.join(ret)
class Class(Element):
	def __init__(self, model, module, name, table=None):
		Element.__init__(self)
		self.model = model
		self.module = module
		self.name = name
		self.module.registerClass(self)
		self.table = table
		self.fields = []
	def createField(self, dbCol, setterName, getterName, isSetTest=None, isSetExpression=None):
		f = Field(self.model, self.module, self, dbCol, setterName, getterName, isSetTest, isSetExpression)
		self.fields.append(f)
		return f
	def create(self):
		if not self.hasTable():
			raise RuntimeError('{cn}: table is not set'.format(cn=self.__class__.__name__))
		path = self.module.fullPath()
		self.createHeader(path)
		self.createImplementation(path)
	def ctorArguments(self):
		ret = []
		for f in self.fields:
			ret.append(f.paramDecl())
		return ret
	def ctorDeclaration(self):
		return '{cn}({vars});'.format(cn=self.name, vars=', '.join(self.ctorArguments()))
	def ctorImplementation(self):
		ret = ['{cn}::{cn}({vars}):'.format(cn=self.name, vars=', '.join(self.ctorArguments())),
				'\tEntity(),',
				'\t{}'.format(',\n\t'.join(self.varInitList())),
				'{ }']
		return '\n'.join(ret)
	def dtorDeclaration(self):
		return 'virtual ~{cn}();'.format(cn=self.name)
	def dtorImplementation(self):
		ret = ['{cn}::~{cn}() {{ }}'.format(cn=self.name)]
		return '\n'.join(ret)
	def hasTable(self):
		return self.table is not None
	def varInitList(self):
		ret = []
		for f in self.fields:
			ret.append(f.varInit())
		return ret
	def dataVariableDeclarations(self):
		ret = []
		for f in self.fields:
			ret.append(f.varDecl())
		return ret
	def isSetDeclarations(self):
		ret = []
		for f in self.fields:
			if f.hasIsSetTest():
				ret.append(f.isSetDecl())
		return ret
	def isSetImplementations(self):
		ret = []
		for f in self.fields:
			if f.hasIsSetTest():
				ret.append(f.isSetImpl())
		return ret
	def setterDeclarations(self):
		ret = []
		for f in self.fields:
			if f.hasSetter():
				ret.append(f.setterDecl())
		return ret
	def setterImplementations(self):
		ret = []
		for f in self.fields:
			if f.hasSetter():
				ret.append(f.setterImpl())
		return ret
	def getterDeclarations(self):
		ret = []
		for f in self.fields:
			if f.hasGetter():
				ret.append(f.getterDecl())
		return ret
	def getterImplementations(self):
		ret = []
		for f in self.fields:
			if f.hasGetter():
				ret.append(f.getterImpl())
		return ret
	
	def createHeader(self, path):
		buf = ['// automatially generated class declaration for class {}'.format(self.name),
				'#include <orm/Entity.h>',
				'',
				'class {cn}: public Entity {{'.format(cn=self.name),
				'public:',
				'\t{}'.format(self.ctorDeclaration()),
				'\t{}'.format(self.dtorDeclaration()),
				'',
				'\t{}'.format('\n\t'.join(self.isSetDeclarations())),
				'',
				'\t{}'.format('\n\t'.join(self.setterDeclarations())),
				'',
				'\t{}'.format('\n\t'.join(self.getterDeclarations())),
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
				'',
				'\n\n'.join(self.isSetImplementations()),
				'',
				'\n\n'.join(self.setterImplementations()),
				'',
				'\n\n'.join(self.getterImplementations())]
		self.writeToFile('{p}/{n}.cpp'.format(p=path, n=self.name), buf)
	def writeToFile(self, fn, buf):
		f = open(fn, 'w')
		f.write('\n'.join(buf))
		f.write('\n')
		f.close()
	
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
	def cppTypeFromDbCol(self, dbCol):
		return self.fieldTypeFromDbType(dbCol.type).cppType
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