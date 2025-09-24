# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

This file is a proprietary product, not an open-source one.
"""

# stdlib
import ast
import logging
import os

# diskcache
from diskcache import Cache

# tqdm
from tqdm import tqdm

# ################################################################################################################################
# ################################################################################################################################

# Logger for this module
logger = logging.getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

class TypeConversionError(Exception):
    """ Raised when a type cannot be converted to an OpenAPI type.
    """

# ################################################################################################################################
# ################################################################################################################################

class IOVisitor(ast.NodeVisitor):
    """ AST visitor that extracts I/O definitions from service classes and model classes.
    """
    def __init__(self):
        self.services = []
        self.models = {}
        self.current_class = None
        self.is_service = False
        self.is_model = False
        self.service_name = None
        self.service_input = None
        self.service_output = None
        self.model_fields = {}
        self.handle_method_exists = False

    def visit_ClassDef(self, node):
        """ Visit class definitions to identify services and models.
        """
        prev_class = self.current_class
        prev_is_service = self.is_service
        prev_is_model = self.is_model
        prev_model_fields = self.model_fields

        self.current_class = node.name
        self.is_service = False
        self.is_model = False
        self.service_name = None
        self.service_input = None
        self.service_output = None
        self.model_fields = {}

        # Check if the class inherits from Service or RESTAdapter
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Service', 'RESTAdapter'):
                self.is_service = True
                break
            # Check if this is a Model class
            elif isinstance(base, ast.Name) and base.id == 'Model':
                self.is_model = True
                break

        # Visit all class contents
        for item in node.body:
            self.visit(item)

        # If this is a service, collect its information
        if self.is_service and self.service_name:
            service_info = {
                'name': self.service_name,
                'class_name': self.current_class,
                'input': self.service_input,
                'output': self.service_output,
                'has_handle_method': self.handle_method_exists
            }
            self.services.append(service_info)

        # If this is a model, collect its field information
        if self.is_model and self.model_fields:
            self.models[self.current_class] = self.model_fields

        self.current_class = prev_class
        self.is_service = prev_is_service
        self.is_model = prev_is_model
        self.model_fields = prev_model_fields

    def visit_AnnAssign(self, node):
        """ Visit annotated assignments to find model field definitions.
        """
        if not self.current_class or not self.is_model:
            return

        # Handle model field annotations
        if isinstance(node.target, ast.Name):
            field_name = node.target.id
            field_type = self._parse_annotation(node.annotation)
            field_default = None

            # Check if there's a default value
            if node.value:
                if isinstance(node.value, ast.Constant):
                    field_default = node.value.value
                elif isinstance(node.value, ast.Name) and node.value.id == 'None':
                    field_default = None

            self.model_fields[field_name] = {
                'type': field_type,
                'default': field_default,
                'required': field_default is None and not isinstance(field_type, dict)
                                      or (isinstance(field_type, dict) and field_type.get('optional') is False)
            }

    def _parse_annotation(self, annotation):
        """ Parse type annotations for model fields.
        """
        # Handle simple types
        if isinstance(annotation, ast.Name):
            return annotation.id

        # Handle subscripted types like list_[Type], union_[Type1, Type2], etc.
        if isinstance(annotation, ast.Subscript):
            container_type = self._get_name_from_node(annotation.value)

            # Handle list_[Type] or List[Type]
            if container_type in ('list_', 'List'):
                element_type = self._get_name_from_node(annotation.slice)

                return {
                    'container': 'list',
                    'element_type': element_type
                }

            # Handle Optional[Type] or optional[Type]
            if container_type in ('optional', 'Optional'):
                element_type = self._get_name_from_node(annotation.slice)

                return {
                    'type': element_type,
                    'optional': True
                }

            # Handle Union types: union_[Type1, Type2]
            if container_type in ('union_', 'Union'):
                # Extract all union types
                union_types = []

                # Check if it's a slice with a tuple of types
                if isinstance(annotation.slice, ast.Tuple):
                    # Multiple types in the union
                    for elt in annotation.slice.elts:
                        type_name = self._get_name_from_node(elt)
                        union_types.append(type_name)
                else:
                    # Single type in the union (unusual but possible)
                    type_name = self._get_name_from_node(annotation.slice)
                    union_types.append(type_name)

                return {
                    'type': 'union',
                    'container': 'union',
                    'union_types': union_types  # Store all possible types
                }

            # Handle other container types - map to generic object
            return {
                'container': container_type,
                'element_type': 'object'
            }

        # Handle other AST node types by mapping them to basic types
        if isinstance(annotation, ast.Attribute):
            # Handle attribute access like module.Type
            return 'object'

        if isinstance(annotation, ast.Tuple):
            # Handle tuple types
            return {
                'container': 'tuple',
                'element_type': 'object'
            }

        # As a last resort, map to 'object' instead of raising an exception
        # This ensures we don't stop processing due to one unknown type
        logger.warning(f'Mapping unknown type annotation {annotation.__class__.__name__} to generic object')
        return 'object'

    def _get_name_from_node(self, node):
        """ Extract name from an AST node.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Subscript):
            # Handle nested subscripts
            return {
                'container': self._get_name_from_node(node.value),
                'element_type': self._get_name_from_node(node.slice)
            }
        raise TypeConversionError(f'Unrecognized node type: {node.__class__.__name__}')

    def visit_Assign(self, node):
        """ Visit assignments to find service attributes like name, input, output.
        """
        if not self.current_class:
            return

        # Check for service attributes
        if self.is_service:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Check for name attribute
                    if target.id == 'name' and isinstance(node.value, ast.Constant):
                        self.service_name = node.value.value

                    # Check for input attribute
                    elif target.id == 'input':
                        if isinstance(node.value, ast.Name):
                            # Input as a model class
                            self.service_input = {'type': 'model', 'model_name': node.value.id}
                        elif isinstance(node.value, ast.Constant):
                            # Input as a string
                            input_value = node.value.value
                            self.service_input = {'type': 'string', 'name': input_value}

                            # Check if input parameter is optional (starts with -)
                            if input_value.startswith('-'):
                                self.service_input['required'] = False
                                self.service_input['name'] = input_value[1:]
                            else:
                                self.service_input['required'] = True

                        elif isinstance(node.value, ast.Tuple):
                            # Input as a tuple of strings
                            elts = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    param_value = elt.value
                                    param_info = {
                                        'name': param_value,
                                        'required': True
                                    }

                                    # Check if parameter is optional (starts with -)
                                    if param_value.startswith('-'):
                                        param_info['name'] = param_value[1:]
                                        param_info['required'] = False

                                    elts.append(param_info)

                            if elts:
                                self.service_input = {'type': 'tuple', 'elements': elts}
                        elif isinstance(node.value, ast.Subscript):
                            # Handle list_[ModelClass] or similar
                            container_type = self._get_name_from_node(node.value.value)
                            element_type = self._get_name_from_node(node.value.slice)

                            self.service_input = {
                                'type': 'container',
                                'container_type': container_type,
                                'element_type': element_type
                            }

                    # Check for output attribute
                    elif target.id == 'output':
                        if isinstance(node.value, ast.Name):
                            # Output as a model class
                            self.service_output = {'type': 'model', 'model_name': node.value.id}
                        elif isinstance(node.value, ast.Subscript):
                            # Handle list_[ModelClass] or similar
                            container_type = self._get_name_from_node(node.value.value)
                            element_type = self._get_name_from_node(node.value.slice)

                            self.service_output = {
                                'type': 'container',
                                'container_type': container_type,
                                'element_type': element_type
                            }

    def visit_FunctionDef(self, node):
        """ Visit function definitions to find handle() method.
        """
        if self.current_class and self.is_service and node.name == 'handle':
            self.handle_method_exists = True

# ################################################################################################################################
# ################################################################################################################################

class TypeMapper:
    """ Maps Zato types to OpenAPI types.
    """
    # Basic type mappings
    BASIC_TYPES = {
        'str': {'type': 'string'},
        'str_': {'type': 'string'},
        'strnone': {'type': 'string', 'nullable': True},
        'int': {'type': 'integer', 'format': 'int32'},
        'intnone': {'type': 'integer', 'format': 'int32', 'nullable': True},
        'float': {'type': 'number', 'format': 'float'},
        'floatnone': {'type': 'number', 'format': 'float', 'nullable': True},
        'bool': {'type': 'boolean'},
        'boolnone': {'type': 'boolean', 'nullable': True},
        'bytes': {'type': 'string', 'format': 'binary'},
        'bytesnone': {'type': 'string', 'format': 'binary', 'nullable': True},
        'datetime_': {'type': 'string', 'format': 'date-time'},
        'datetimez': {'type': 'string', 'format': 'date-time'},
        'date': {'type': 'string', 'format': 'date'},
        'decimal_': {'type': 'number'},
        'dict_': {'type': 'object'},
        'object': {'type': 'object'},
        'strlist': {'type': 'array', 'items': {'type': 'string'}},
        'strlistnone': {'type': 'array', 'items': {'type': 'string'}, 'nullable': True},
        'anylist': {'type': 'array', 'items': {'type': 'object'}},
        'anylistnone': {'type': 'array', 'items': {'type': 'object'}, 'nullable': True},
        'dictlist': {'type': 'array', 'items': {'type': 'object'}},
        'union': {'type': 'object'},
        'tuple': {'type': 'array', 'items': {'type': 'object'}},
        'CompletedCourse': {'type': 'object', 'properties': {'id': {'type': 'string'}}},
    }

    def __init__(self):
        self.schema_components = {}
        self.registered_models = set()

    def map_type(self, zato_type, model_definitions=None):
        """ Map a Zato type to an OpenAPI type.
        """
        model_definitions = model_definitions or {}

        # Handle basic types
        if isinstance(zato_type, str) and zato_type in self.BASIC_TYPES:
            return self.BASIC_TYPES[zato_type]

        # Handle model references
        if isinstance(zato_type, str) and zato_type in model_definitions:
            try:
                self._register_model_schema(zato_type, model_definitions)
                return {'$ref': f'#/components/schemas/{zato_type}'}
            except TypeConversionError as e:
                # Add more context about the model
                file_path = 'unknown_file'
                if isinstance(model_definitions.get(zato_type), dict) and 'file_path' in model_definitions.get(zato_type, {}):
                    file_path = model_definitions[zato_type]['file_path']
                raise TypeConversionError(f'Error with model {zato_type} from file {file_path}: {e}')

        # Handle container types like list_[Type] or List[Type]
        if isinstance(zato_type, dict) and 'container' in zato_type:
            container_type = zato_type['container']

            # Handle union types with oneOf schema
            if container_type == 'union' and 'union_types' in zato_type:
                union_types = zato_type['union_types']
                one_of_schemas = []

                # Map each type in the union
                for type_name in union_types:
                    try:
                        mapped_type = self.map_type(type_name, model_definitions)
                        one_of_schemas.append(mapped_type)
                    except TypeConversionError as e:
                        logger.warning(f'Could not map union type {type_name}: {e}')

                # Return oneOf schema if we have any valid types
                if one_of_schemas:
                    return {
                        'oneOf': one_of_schemas
                    }
                else:
                    return {
                        'anyOf': [
                            {'type': 'string'},
                            {'type': 'number'},
                            {'type': 'object'},
                            {'type': 'array', 'items': {'type': 'object'}}
                        ]
                    }

            # Handle list-like containers
            element_type = zato_type.get('element_type', 'object')
            if container_type in ('list', 'list_', 'List'):
                return {
                    'type': 'array',
                    'items': self.map_type(element_type, model_definitions)
                }

        # Handle optional types
        if isinstance(zato_type, dict) and 'optional' in zato_type and zato_type['optional']:
            mapped_type = self.map_type(zato_type['type'], model_definitions)
            mapped_type['nullable'] = True # type: ignore
            return mapped_type

        # If we can't map the type, raise an exception
        raise TypeConversionError(f'Cannot map Zato type \'{zato_type}\' to OpenAPI type. Add this type to BASIC_TYPES in TypeMapper class')

    def _register_model_schema(self, model_name, model_definitions):
        """ Register a model schema in the components section.
        """
        if model_name in self.registered_models:
            return

        model_def = model_definitions.get(model_name)
        if not model_def:
            raise TypeConversionError(f'Model \'{model_name}\' not found in definitions')

        properties = {}
        required = []

        # Extract file path information if available
        file_path = 'unknown_file'
        if isinstance(model_def, dict) and 'file_path' in model_def:
            file_path = model_def['file_path']
            fields = model_def.get('fields', {})
        else:
            fields = model_def

        for field_name, field_info in fields.items():
            field_type = field_info['type']
            try:
                properties[field_name] = self.map_type(field_type, model_definitions)

                # Add to required list if the field is required
                if field_info.get('required', True):
                    required.append(field_name)
            except TypeConversionError as e:
                # Re-raise with additional context
                raise TypeConversionError(f'Error mapping field \'{field_name}\' in model \'{model_name}\' (from {file_path}): {str(e)}')

        schema = {
            'type': 'object',
            'properties': properties
        }

        if required:
            schema['required'] = required

        self.schema_components[model_name] = schema
        self.registered_models.add(model_name)

    def get_schema_components(self):
        """ Get all registered schema components.
        """
        return self.schema_components

# ################################################################################################################################
# ################################################################################################################################

class IOScanner:
    """ Scans directories for Zato services and extracts their I/O information.
    """
    def __init__(self, cache_dir='/tmp/zato_io_scanner_cache'):
        self.cache = Cache(cache_dir)
        self.type_mapper = TypeMapper()

    def is_python_file(self, file_path):
        """ Check if a file is a Python file.
        """
        return file_path.endswith('.py')

    def get_file_mtime(self, file_path):
        """ Get the modification time of a file.
        """
        return os.path.getmtime(file_path)

    def scan_file(self, file_path):
        """ Scan a single Python file for services and models.
        """
        # Check cache first
        mtime = self.get_file_mtime(file_path)
        cache_key = f'{file_path}:{mtime}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = {'services': [], 'models': {}}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
                visitor = IOVisitor()
                visitor.visit(tree)

                # Add file path to all services for better error tracking
                for service in visitor.services:
                    service['file_path'] = file_path

                # Create a copy of models with file path information
                models_with_path = {}
                for model_name, model_info in visitor.models.items():
                    models_with_path[model_name] = {
                        'fields': model_info,
                        'file_path': file_path
                    }

                result['services'] = visitor.services
                result['models'] = models_with_path

            # Store in cache
            self.cache[cache_key] = result
        except Exception as e:
            error_msg = f'Error parsing {file_path}: {e}'
            logger.error(error_msg)
            # Add stack trace for better debugging
            logger.error('Stack trace: ', exc_info=True)

        return result

    def scan_directory(self, directory):
        """ Recursively scan a directory for services and models.
        """
        all_results = {'services': [], 'models': {}}
        py_files = []

        # Find all Python files in the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if self.is_python_file(file):
                    py_files.append(os.path.join(root, file))

        # Scan each Python file with progress bar
        for file_path in tqdm(py_files, desc=f'Scanning {directory}'):
            file_results = self.scan_file(file_path)
            all_results['services'].extend(file_results['services']) # type: ignore
            all_results['models'].update(file_results['models']) # type: ignore

        return all_results

    def scan_directories(self, directories):
        """ Scan multiple directories for services and models.
        """
        all_results = {'services': [], 'models': {}}
        for directory in directories:
            results = self.scan_directory(directory)
            all_results['services'].extend(results['services'])

            # Preserve file path information when merging models
            for model_name, model_info in results['models'].items():
                all_results['models'][model_name] = model_info

        return all_results

# ################################################################################################################################
# ################################################################################################################################

def scan_io(directories, output_file):
    """ Scan directories for services and generate an OpenAPI specification with I/O information.
    """
    # Import here to avoid circular imports
    from zato.openapi.generator.openapi_ import OpenAPIGenerator

    # Scan for services and models
    scanner = IOScanner()
    scan_results = scanner.scan_directories(directories)

    # Generate OpenAPI specification using the separate generator
    openapi_generator = OpenAPIGenerator(scanner.type_mapper)
    openapi_generator.generate_openapi(scan_results, output_file)

    logger.info(f'Found {len(scan_results["services"])} services and {len(scan_results["models"])} models. ' + \
               f'OpenAPI specification saved to {output_file}')

# ################################################################################################################################
# ################################################################################################################################
