from autocomplete import extract_symbols

def format_symbol_suggestion(suggestions):
    imports = suggestions['imports'] + suggestions['imports_as'] + suggestions['imports_from']
    relative_imports = suggestions['imports_relative']
    global_vars = suggestions['global_vars']
    functions = suggestions['functions']
    classes = suggestions['class_def']

    rtn = {'import_package_or_function': imports, 
            'relative_import': relative_imports,
            'global_variable': global_vars,
            'mannual_defined_function': functions,
            'mannual_defined_class': classes}
    rtn = {k:v for k,v in rtn.items() if len(v) > 0}
    return "\n".join([k + ": " + ", ".join([e[0] for e in v]) for k,v in rtn.items()]), rtn
def extract(each_content):
    api_calls, suggestions = extract_symbols(each_content)
    suggestions, suggestion_loc = format_symbol_suggestion(suggestions)
    symbol_dict = {}
    for k in suggestion_loc:
        for e in suggestion_loc[k]:
            symbol_dict[e[0]] = {"type": k, "code": e[1]}
    rst = { "symbols": symbol_dict, "content": each_content}
    return rst


if __name__ == "__main__":
    with open("code_example.py",'r') as f:
        content = f.read()
    rst = extract(content)
    print(rst['symbols'].keys())
    # print(rst)