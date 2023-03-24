""" Autocomplete utility

    Usage:

    ac = Autocomplete(tree, code_bytes, pos)
    suggestions = ac.autocomplete(cursor_byte)
"""

import argparse
import queries
from tree_sitter import Language, Parser

PY_LANGUAGE = Language('build/python.so', 'python')

class Autocomplete():
    def __init__(self, tree, code_bytes, pos):
        self.tree = tree
        self.code_bytes = code_bytes
        self.pos = pos
        self.valid_class_scope = []
        self.valid_func_scope = []

    def get_node_value(self, node):
        return self.code_bytes[node.start_byte:node.end_byte]
    
    def byte_within_scope(self, scope, byte_pos=None):
        """ Checks if pos (byte) is within scope (byte range).

        Args:
            scope: Tuple of (start_byte, end_byte)
            cursor_byte: Byte position of interest
        """
        if cursor_byte is None or len(scope) != 2:
            return False
        return scope[0] <= cursor_byte and scope[1] >= cursor_byte
    
    def parse_functions(self):
        functions = []
        for child in self.tree.root_node.children:
            # If the function has an identifier, keep track of it
            if child.type == 'function_definition' and len(child.children) >= 2:
                functions.append(self.get_node_value(child.children[1]).decode("utf-8"))
        return functions
    
    def parse_globals(self):
        global_vars = []
        for child in self.tree.root_node.children:
            if child.type == 'expression_statement':
                global_vars.append(self.get_node_value(child).decode("utf-8"))
        global_vars = [global_var.split()[0] for global_var in global_vars]
        return global_vars
    
    def parse_with_query(self, query_str):
        """ Utility function to make queries against the tree.

        Args:
            query_str: Query string. Usually defined in queries.py config file.
        
        Returns:
            List of str with query results
        """
        query = PY_LANGUAGE.query(query_str)
        captures = query.captures(self.tree.root_node)
        return [self.get_node_value(capture[0]).decode('utf-8') for capture in captures]
    
    def get_node_children_value_given_type(self, node, given_type="identifier"):
        """ Utility function to get the value of a node's children given a type.

        Args:
            node: Tree-sitter node
            given_type: Type of node to look for
        
        Returns:
            List of str with query results
        """
        return [self.get_node_value(child).decode('utf-8') for child in node.children if child.type == given_type]

    
    def parse_vars_funcs_in_scope(self, cursor_byte):
        """ Based on the cursor location (byte) recurses through the
            code tree and identifies variables defined in functions
            class variables, and functions in scope
        
        Args:
            cursor_byte: Cursor pos (int of the byte)
        
        Returns:
            Tuple of (class variables, function variables, functions in scope)
        """
        class_vars = []
        func_vars = []
        funcs_in_scope = []
        func_paras = []
        # Recurse through parse tree
        def traverse(node):
            for child in node.children:
                if child.type == 'class_definition' and \
                    self.byte_within_scope([child.start_byte, child.end_byte], cursor_byte):
                    self.valid_class_scope = [child.start_byte, child.end_byte]

                # DFS should iterate through broad scopes to the narrowest possible func scope
                if child.type == 'function_definition' and \
                    self.byte_within_scope([child.start_byte, child.end_byte], cursor_byte):
                    # Check if code_bytes is within this function definition
                    self.valid_func_scope = [child.start_byte, child.end_byte]
                    # If this function is within the class definition, also return the method in scope
                    if self.byte_within_scope(self.valid_class_scope, 
                        child.start_byte) and len(child.children) >= 2:
                        funcs_in_scope.append(self.get_node_value(child.children[1]).decode("utf-8"))
                
                if child.type == 'assignment':
                    # Check if in class scope
                    if self.byte_within_scope(self.valid_class_scope, child.start_byte):
                        class_vars.append(self.get_node_value(child).decode("utf-8"))
                    # Check if in function scope and before cursor position
                    if self.byte_within_scope(self.valid_func_scope, child.start_byte) and child.start_byte <= cursor_byte:
                        func_vars.append(self.get_node_value(child).decode("utf-8"))
                if child.type == 'parameters':
                    # Check if in function scope
                    if self.byte_within_scope(self.valid_func_scope, child.start_byte) and child.start_byte <= cursor_byte:
                        children_identifiers = self.get_node_children_value_given_type(child)
                        func_paras.extend(children_identifiers)
                
                traverse(child)

        traverse(self.tree.root_node)
        # Grab class variable names from assignment string
        # class_vars = ['self.name = name', 'self.address = address', 'abc = [5, 3]', 'xyz = "Hi"']
        class_vars = [class_var.split("=")[0].strip().split('.')[-1] 
            for class_var in class_vars if class_var.startswith('self.')]
        # Grab function variables from assignment
        func_vars = [func_var.split()[0] for func_var in func_vars]
        return class_vars, func_vars, funcs_in_scope, func_paras

    def autocomplete(self, cursor_byte, prev_text=""):
        """ Analyzes source code and uses the cursor position to
            provide a list of possible string completions
            (i.e globals, imports, methods, function, variables, etc. in scope)
        
        Args:
            cursor_byte: Cursor pos (int of the byte)
            prev_text: String for text at cursor
        
        Returns:
            If trailing chars were .self - autocomplete class vars and funcs
            Otherwise - autocomplete globals, imports, vars in scope, and funcs
        """
        # Autocomplete globals, variables in scope, functions, or methods
        # Identify list of globals, functions or methods (regardless of code loc)
        global_vars = self.parse_globals()
        # global_vars = self.parse_with_query(queries.globals_query)
        # functions = self.parse_with_query(queries.functions_query)
        imports = self.parse_with_query(queries.imports_query)
        imports_as = self.parse_with_query(queries.imports_as_query)
        functions = self.parse_functions()

        # print("global_vars", global_vars)
        # print("imports", imports)
        # print("imports_as", imports_as)
        # print("functions", functions)

        class_vars, func_vars, funcs_in_scope, func_paras = self.parse_vars_funcs_in_scope(cursor_byte)
        suggestions = []
        line_len = len(prev_text)
        prev_token = prev_text.split()[-1] if line_len > 0 else ''
        # When trailing chars are 'self.' only add class vars and funcs
        if line_len >= 5 and 'self.' in prev_token:
            suggestions.extend(class_vars)
            suggestions.extend(funcs_in_scope)
            prev_token = prev_token.split('.')[-1]
        else:
            for l in [global_vars, imports, func_vars, functions, func_paras, imports_as]:
                suggestions.extend(l)

        # Filter for text in the last line
        suggestions = [s for s in suggestions if s.startswith(prev_token)]
        suggestions = list(set(suggestions))
        
        return suggestions


def handle_cursor_pos(file, pos):
    """ Reads file line by line to get the byte position of the given cursor
        position and also grabs the text that comes before the cursor (on the line).

        Args:
            file: String for file location.
            pos: Cursor position integer
        
        Returns:
            A tuple of (cursor_byte, prev_text)
    """
    if pos <= 0:
        return (0, None)

    with open(file, 'rb') as f:
        # Account for 1-indexed lines
        for line_num in range(pos-1):
            f.readline()
        cursor_byte = f.tell() # Cursor position in bytes

        # Decodes bytes to string and strip trailing chars
        prev_text = f.readline().decode("utf-8").rstrip()
        return cursor_byte, prev_text


if __name__ == "__main__":
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Autocomplete utility")
    parser.add_argument(
        '--file',
        dest='file',
        type=str,
        help='The file path to source code.',
        required=True)
    parser.add_argument(
        '--pos',
        dest='pos',
        type=int,
        help='Cursor position in source code',
        required=True
    )
    args = parser.parse_args()

    # Parse source code into tree
    code_bytes = open(args.file, "rb").read() # May want to check if invalid read

    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    tree = parser.parse(code_bytes)
    
    cursor_byte, prev_text = handle_cursor_pos(args.file, args.pos)
    # print(prev_text)
    completer = Autocomplete(tree, code_bytes, args.pos)
    suggestions = completer.autocomplete(cursor_byte, prev_text)
    print(suggestions)