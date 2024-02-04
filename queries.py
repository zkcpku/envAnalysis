""" Tree-Sitter Query strings
"""

functions_query = """
    (function_definition
        name: (identifier) @function.def)
"""

imports_query = """
    (import_statement
        name: (dotted_name (identifier) @import-name))
"""

globals_query = """
    (expression_statement
        (assignment left: (expression_list (identifier) @var-name)))
"""

# example: import numpy as np
# module [0, 0] - [2, 0]
#   import_statement [0, 0] - [0, 18]
#     name: aliased_import [0, 7] - [0, 18]
#       name: dotted_name [0, 7] - [0, 12]
#         identifier [0, 7] - [0, 12]
#       alias: identifier [0, 16] - [0, 18]

imports_and_as_query = """
    (import_statement
        name: (aliased_import
            name: (dotted_name (identifier) @import-name)
            alias: (identifier) @import-as))
"""
imports_as_query = """
    (import_statement
        name: (aliased_import
            name: (dotted_name (identifier))
            alias: (identifier) @import-as))
"""

#   import_from_statement [5, 0] - [5, 22]
#     module_name: dotted_name [5, 5] - [5, 11]
#       identifier [5, 5] - [5, 11]
#     name: dotted_name [5, 19] - [5, 20]
#       identifier [5, 19] - [5, 20]
#     name: dotted_name [5, 21] - [5, 22]
#       identifier [5, 21] - [5, 22]
# and即既包含from后面的 又包含import后面的
imports_and_from_query = """
    (import_from_statement
        module_name: (dotted_name (identifier) @import-name)
        name: (dotted_name (identifier) @import-from))
"""

imports_from_query = """
    (import_from_statement
        module_name: (dotted_name (identifier) @import-name)
        name: (dotted_name (identifier) @import-from))
"""

# from .distance_metrics import euclidean
#   import_from_statement [6, 0] - [6, 39]
#     module_name: relative_import [6, 5] - [6, 22]
#       import_prefix [6, 5] - [6, 6]
#       dotted_name [6, 6] - [6, 22]
#         identifier [6, 6] - [6, 22]
#     name: dotted_name [6, 30] - [6, 39]
#       identifier [6, 30] - [6, 39]
imports_relative_query = """
    (import_from_statement
        module_name: (relative_import
            )  
        name: (dotted_name (identifier) @import-name))
"""

class_def_query = """
    (class_definition
        name: (identifier) @class-name
        body: (block)
        )
"""


api_query = """
    (call
        function: (attribute
            object: (identifier) @api.object
            attribute: (identifier) @api.attribute))
"""

api_function_query = """
    (call
        function: (identifier) @api.function)
"""

api_and_api_function_query = """
    (call
        [function: (attribute
            object: (identifier) @api.object
            attribute: (identifier) @api.attribute)
        function: (identifier) @api.function])
"""

whole_api_and_api_function = """
    (call
        [function: (attribute) @api.attribute
        function: (identifier) @api.function])
"""