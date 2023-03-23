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