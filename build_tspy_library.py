from tree_sitter import Language, Parser

Language.build_library(
  'build/languages.so',

  [
    'vendor/tree-sitter-javascript',
    'vendor/tree-sitter-python'
  ]
)

PY_LANGUAGE = Language('build/languages.so', 'python')
JS_LANGUAGE = Language('build/languages.so', 'javascript')

parser = Parser()
# parser.set_language(JS_LANGUAGE)


parser.set_language(PY_LANGUAGE)

tree = parser.parse(bytes("""
def foo():
    if bar:
        baz()
""", "utf8"))

root_node = tree.root_node
import ipdb; ipdb.set_trace()
assert root_node.type == 'module'
assert root_node.start_point == (1, 0)
assert root_node.end_point == (3, 13)