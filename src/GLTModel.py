from DbModel import Database, Schema, OrderStatement

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
    def createCore(self):
        self.tTags = self.createTags()
        self.tSiPrefixes = self.createSiPrefixes()
        self.tUnits = self.createUnits()
        self.tConstants = self.createConstants()
        self.tSVGElements = self.createSVGElements()
        self.tProjectElementTypes = self.createProjectElementTypes()
        self.tProjectElements = self.createProjectElements()
    def createGeology(self):
        self.tRockClasses = self.createRockClasses()
        self.tRocks = self.createRocks()
        self.tSedimentFeatureTypes = self.createSedimentFeatureTypes()
        self.tSedimentFeatures = self.createSedimentFeatures()
        self.tGeologicUnitTypes = self.createGeologicUnitTypes()
        self.tAgeModelElementTypes = self.createAgeModelElementTypes()
        self.tAgeModelElements = self.createAgeModelElements()
        self.tGrainSizeTypes = self.createGrainSizeTypes()
        self.tGrainSizes = self.createGrainSizes()
        self.tOutcrops = self.createOutcrops()
        self.tProfileTypes = self.createProfileTypes()
        self.tProfiles = self.createProfiles()
        self.tProfileColumns = self.createProfileColumns()
        self.tAssignedProfileColumns = self.createAssignedProfileColumns()
    def createAssignedProfileColumns(self):
        t = self.schemaGeology.createTable('profiles_profile_columns')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_profiles_profile_columns'))
        profile_id = t.createColumn('profile_id', self.tInt, nullable=False, referencedColumn=self.tProfiles.primaryKey.firstColumn())
        profile_column_id = t.createColumn('profile_column_id', self.tInt, nullable=False, referencedColumn=self.tProfileColumns.primaryKey.firstColumn())
        position = t.createColumn('position', self.tInt, nullable=False, defaultValue=1)
        t.createPrimaryKey([id])
        t.createUniqueConstraint([profile_id, profile_column_id])
        t.createUniqueConstraint([profile_id, position])
        t.createCreateProcedure(self.schemaLogic, 'assign_column_to_profile', [profile_column_id, profile_id, position])
        t.createUpdateProcedure(self.schemaLogic, 'update_column_in_profile', [id, profile_column_id, profile_id, position])
        t.createGetAllProcedure(self.schemaLogic, 'get_all_columns_in_all_profiles', [OrderStatement(profile_id, True),
                                                                                      OrderStatement(profile_column_id, True),
                                                                                      OrderStatement(position, True)])
        return t
    def createProfileColumns(self):
        return self.createStandardTable(self.schemaGeology, 'create_profile_columns', 
                                        createProcedureName='create_profile_column', 
                                        updateProcedureName='update_profile_column', 
                                        deleteProcedureName='delete_profile_column', 
                                        getAllProcedureName='get_all_profile_columns')
    def createProfileTypes(self):
        return self.createStandardTable(self.schemaGeology, 'profile_types',
                                        createProcedureName='create_profile_type',
                                        updateProcedureName='update_profile_type',
                                        deleteProcedureName='delete_profile_type',
                                        getAllProcedureName='get_all_profile_types')
    def createProfiles(self):
        t = self.schemaGeology.createTable('profiles')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_profiles'))
        type_id = t.createColumn('profile_type_id', self.tInt, nullable=False, referencedColumn=self.tProfileTypes.primaryKey.firstColumn())
        project_element_id = t.createColumn('project_element_id', self.tInt, nullable=False, referencedColumn=self.tProjectElements.primaryKey.firstColumn())
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Profile')
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([project_element_id, name])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_profile', [name, code, type_id, project_element_id, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_profile', [id, name, code, type_id, project_element_id, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_profile', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_profiles', [OrderStatement(name, True)])
        return t
    def createOutcrops(self):
        t = self.schemaGeology.createTable('outcrops')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_outcrops'))
        lat = t.createColumn('lat', self.tNumeric, nullable=True)
        lon = t.createColumn('lon', self.tNumeric, nullable=True)
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Outcrop')
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_outcrop', [name, code, lat, lon, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_outcrop', [id, name, code, lat, lon, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_outcrop', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_outcrops', [OrderStatement(lat, True),
                                                                       OrderStatement(lon, True)])
        return t
    def createProjectElements(self):
        t = self.schemaCore.createTable('project_elements')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_project_elements'))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True, referencedColumn=id)
        type_id = t.createColumn('project_element_type_id', self.tInt, nullable=False, referencedColumn=self.tProjectElementTypes.primaryKey.firstColumn())
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Project Element')
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([parent_id, name])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_project_element', [name, type_id, parent_id, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_project_element', [id, name, type_id, parent_id, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_project_element', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_project_elements', [OrderStatement(name, True)])
        return t
    def createProjectElementTypes(self):
        return self.createStandardTable(self.schemaCore, 'project_element_types', 
                                        createProcedureName='create_project_element_type', 
                                        updateProcedureName='update_project_element_type', 
                                        deleteProcedureName='delete_project_element_type', 
                                        getAllProcedureName='get_all_project_element_types')
    def createGrainSizes(self):
        t = self.schemaGeology.createTable('grain_sizes')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_grain_sizes'))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True, referencedColumn=id)
        type_id = t.createColumn('grain_size_type_id', self.tInt, nullable=False)
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Grain Size')
        code = t.createColumn('code', self.tText, nullable=True)
        symbol = t.createColumn('symbol', self.tText, nullable=False)
        min_size_value = t.createColumn('min_size', self.tNumeric, nullable=False, defaultValue=0.0)
        min_size_unit_id = t.createColumn('min_size_unit_id', self.tInt, nullable=False, referencedColumn=self.tUnits.primaryKey.firstColumn())
        max_size_value = t.createColumn('max_size', self.tNumeric, nullable=False, defaultValue=0.0)
        max_size_unit_id = t.createColumn('max_size_unit_id', self.tInt, nullable=False, referencedColumn=self.tUnits.primaryKey.firstColumn())
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([type_id, name, parent_id])
        t.createUniqueConstraint([parent_id, type_id])
        t.createUniqueConstraint([parent_id, symbol])
        t.createAuditTable(self.schemaAudit)
        t.createUniqueConstraint([min_size_value, min_size_unit_id, max_size_value, max_size_unit_id, parent_id])
        t.createCreateProcedure(self.schemaLogic, 'create_grain_size', 
                                [name, code, symbol,
                                 type_id, parent_id, 
                                 min_size_value, min_size_unit_id,
                                 max_size_value, max_size_unit_id,
                                 description])
        t.createUpdateProcedure(self.schemaLogic, 'update_grain_size', 
                                [id, name, code, symbol,
                                 type_id, parent_id, 
                                 min_size_value, min_size_unit_id,
                                 max_size_value, max_size_unit_id,
                                 description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_grain_size', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_grain_sizes', [OrderStatement(name, True),
                                                                          OrderStatement(min_size_value, True),
                                                                          OrderStatement(min_size_unit_id, True)])
        return t
    def createAgeModelElements(self):
        t = self.schemaGeology.createTable('age_model_elements')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_age_model_elements'))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True, referencedColumn=id)
        type_id = t.createColumn('age_model_element_type_id', self.tInt, nullable=False, referencedColumn=self.tAgeModelElementTypes.primaryKey.firstColumn())
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Age Model Element')
        code = t.createColumn('code', self.tText, nullable=True)
        symbol = t.createColumn('symbol', self.tText, nullable=False, preventEmptyText=False, defaultText='')
        begin_value = t.createColumn('begin_value', self.tNumeric, nullable=True)
        end_value = t.createColumn('end_value', self.tNumeric, nullable=True)
        begin_unit_id = t.createColumn('begin_unit_id', self.tInt, nullable=True, referencedColumn=self.tUnits.primaryKey.firstColumn())
        end_unit_id = t.createColumn('end_unit_id', self.tInt, nullable=True, referencedColumn=self.tUnits.primaryKey.firstColumn())
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name, parent_id])
        t.createUniqueConstraint([code])
        t.createUniqueConstraint([symbol])
        t.createUniqueConstraint([begin_value, begin_unit_id, end_value, end_unit_id])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_age_model_element', 
                                [name, code, symbol, 
                                 type_id, parent_id, 
                                 begin_value, begin_unit_id, 
                                 end_value, end_unit_id, 
                                 description])
        t.createUpdateProcedure(self.schemaLogic, 'update_age_model_element', 
                                [id, name, code, symbol, 
                                 type_id, parent_id, 
                                 begin_value, begin_unit_id, 
                                 end_value, end_unit_id, 
                                 description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_age_model_element', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_age_model_elements', [OrderStatement(name, True)])
        return t
    def createSedimentFeatures(self):
        t = self.schemaGeology.createTable('sediment_features')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_sediment_features'))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True, referencedColumn=id)
        type_id = t.createColumn('sediment_feature_type_id', self.tInt, nullable=False, referencedColumn=self.tSedimentFeatureTypes.primaryKey.firstColumn())
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Name')
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name, parent_id])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_sediment_feature', [name, code, type_id, parent_id, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_sediment_feature', [id, name, code, type_id, parent_id, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_sediment_feature', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_sediment_features', [OrderStatement(name, True)])
        return t
    def createRocks(self):
        t = self.schemaGeology.createTable('rocks')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaGeology.createSequence('seq_rocks'))
        parent_id = t.createColumn('parent_id', self.tInt, nullable=True)
        rock_class_id = t.createColumn('rock_class_id', self.tInt, nullable=False, referencedColumn=self.tRockClasses.primaryKey.firstColumn())
        name = t.createColumn('name', self.tText, nullable=False, defaultText='New Rock', preventEmptyText=True)
        code = t.createColumn('code', self.tText, nullable=True)
        svg_element_id = t.createColumn('svg_element_id', self.tInt, nullable=True, referencedColumn=self.tSVGElements.primaryKey.firstColumn())
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([parent_id, name])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_rock', [name, code, rock_class_id, svg_element_id, parent_id, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_rock', [id, name, code, rock_class_id, svg_element_id, parent_id, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_rock', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_rocks', [OrderStatement(name, True)])
    def createRockClasses(self):
        return self.createStandardHierarchicalTable(self.schemaGeology, 'rock_classes', 
                                                    createProcedureName='create_rock_class',
                                                    updateProcedureName='update_rock_class',
                                                    deleteProcedureName='delete_rock_class',
                                                    getAllProcedureName='get_all_rock_classes')
    def createSedimentFeatureTypes(self):
        return self.createStandardHierarchicalTable(self.schemaGeology, 'sediment_feature_types', 
                                                    createProcedureName='create_sediment_feature_type', 
                                                    updateProcedureName='update_sediment_feature_type', 
                                                    deleteProcedureName='delete_sediment_feature_type', 
                                                    getAllProcedureName='get_all_sediment_feature_types')
    def createGeologicUnitTypes(self):
        return self.createStandardHierarchicalTable(self.schemaGeology, 'geologic_unit_types', 
                                                    createProcedureName='create_geologic_unit_type', 
                                                    updateProcedureName='update_geologic_unit_type', 
                                                    deleteProcedureName='delete_geologic_unit_type', 
                                                    getAllProcedureName='get_all_geologic_unit_types')
    def createGrainSizeTypes(self):
        return self.createStandardHierarchicalTable(self.schemaGeology, 'grain_size_types', 
                                                    createProcedureName='create_grain_size_type', 
                                                    updateProcedureName='update_grain_size_type', 
                                                    deleteProcedureName='delete_grain_size_type', 
                                                    getAllProcedureName='get_all_grain_size_types')
    def createAgeModelElementTypes(self):
        return self.createStandardTable(self.schemaGeology, 'age_model_element_types', 
                                        createProcedureName='create_age_model_element_type', 
                                        updateProcedureName='update_age_model_element_type', 
                                        deleteProcedureName='delete_age_model_element_type', 
                                        getAllProcedureName='get_all_age_model_element_types')
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
    def createStandardTable(self, schema, name,
                            createProcedureName,
                            updateProcedureName,
                            deleteProcedureName,
                            getAllProcedureName):
        t = schema.createTable(name)
        id = t.createColumn('id', self.tInt, nullable=False, sequence=schema.createSequence('seq_{}'.format(name)))
        name = t.createColumn('name', self.tText, nullable=False, defaultText='New Entry', preventEmptyText=True)
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, createProcedureName, [name, code, description])
        t.createUpdateProcedure(self.schemaLogic, updateProcedureName, [id, name, code, description])
        t.createDeleteProcedure(self.schemaLogic, deleteProcedureName, id)
        t.createGetAllProcedure(self.schemaLogic, getAllProcedureName, [OrderStatement(name, True)])
        return t
    def createSVGElements(self):
        t = self.schemaCore.createTable('svg_elements')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_svg_elements'))
        name = t.createColumn('name', self.tText, nullable=False, defaultText='New SVG Element', preventEmptyText=True)
        svg = t.createColumn('svg', self.tText, nullable=True)
        path = t.createColumn('path', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_svg_element', [name, svg, path, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_svg_element', [id, name, svg, path, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_svg_element', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_svg_elements', [OrderStatement(name, True)])
        return t
    def createTags(self):
        return self.createStandardTable(self.schemaCore, 'tags',
                                        createProcedureName='create_tag',
                                        updateProcedureName='update_tag',
                                        deleteProcedureName='delete_tag',
                                        getAllProcedureName='get_all_tags')
        
    def createSiPrefixes(self):
        t = self.schemaCore.createTable('si_prefixes')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_si_prefixes'))
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New SI Prefix')
        symbol = t.createColumn('symbol', self.tText, nullable=False, preventEmptyText=True, defaultText='')
        code = t.createColumn('code', self.tText, nullable=True)
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        factor = t.createColumn('factor', self.tNumeric, nullable=False, preventValue=0.0)
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createUniqueConstraint([symbol])
        t.createUniqueConstraint([code])
        t.createUniqueConstraint([factor])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_si_prefix', [name, code, symbol, factor, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_si_prefix', [id, name, code, symbol, factor, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_si_prefix', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_si_prefixes', [OrderStatement(name, True)])
        return t
    def createUnits(self):
        t = self.schemaCore.createTable('units')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_units'))
        base_unit_id = t.createColumn('base_unit_id', self.tInt, nullable=True, referencedColumn=id)
        name = t.createColumn('name', self.tText, nullable=False, preventEmptyText=True, defaultText='New Unit')
        code = t.createColumn('code', self.tText, nullable=True)
        symbol = t.createColumn('symbol', self.tText, nullable=False, defaultText='Symbol')
        prefix_id = t.createColumn('si_prefix_id', self.tInt, nullable=True, referencedColumn=self.tSiPrefixes.primaryKey.firstColumn())
        description = t.createColumn('description', self.tText, nullable=False, defaultText='')
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createUniqueConstraint([symbol])
        t.createUniqueConstraint([code])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_unit', [name, code, symbol, base_unit_id, prefix_id, description])
        t.createUpdateProcedure(self.schemaLogic, 'update_unit', [id, name, code, symbol, base_unit_id, prefix_id, description])
        t.createDeleteProcedure(self.schemaLogic, 'delete_unit', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_si_prefixes', [OrderStatement(name, True)])
        return t
    def createConstants(self):
        t = self.schemaCore.createTable('constants')
        id = t.createColumn('id', self.tInt, nullable=False, sequence=self.schemaCore.createSequence('seq_constants'))
        name = t.createColumn('name', self.tText, nullable=False, defaultText='New Constant', preventEmptyText=True)
        code = t.createColumn('code', self.tText, nullable=True)
        symbol = t.createColumn('symbol', self.tText, nullable=True)
        unit_id = t.createColumn('unit_id', self.tInt, nullable=True, referencedColumn=self.tUnits.primaryKey.firstColumn())
        value = t.createColumn('numeric_value', self.tNumeric, nullable=False, preventValue=0)
        t.createPrimaryKey([id])
        t.createUniqueConstraint([name])
        t.createUniqueConstraint([code])
        t.createUniqueConstraint([symbol])
        t.createAuditTable(self.schemaAudit)
        t.createCreateProcedure(self.schemaLogic, 'create_constant', [name, code, symbol, value, unit_id])
        t.createUpdateProcedure(self.schemaLogic, 'update_constant', [id, name, code, symbol, value, unit_id])
        t.createDeleteProcedure(self.schemaLogic, 'delete_constant', id)
        t.createGetAllProcedure(self.schemaLogic, 'get_all_constants', [OrderStatement(name, True)])
        return t
    def setupTests(self):
        self.addTest("SELECT * FROM LOGIC.CREATE_TAG('foo', NULL, 'bar');")
        self.addTest("SELECT * FROM LOGIC.UPDATE_TAG(1, 'foobar', NULL, 'barfo');")
        self.addTest("SELECT * FROM LOGIC.DELETE_TAG(1);")
        self.addTest("SELECT LOGIC.GET_ALL_TAGS('all_tags');")
        self.addTest("FETCH ALL IN ALL_TAGS;")
        self.addTest("CLOSE ALL_TAGS;")