import importlib

MODULE2ABBR = {
    "numpy": "np",
    "pandas": "pd",
    "sklearn": "sk",
    "tensorflow": "tf",
    "torch": "torch",
    "keras": "keras",
    "matplotlib": "plt",
    "seaborn": "sns",
    "scipy": "scipy",
    "statsmodels": "sm",
    "gensim": "gensim",
    "nltk": "nltk",
    "spacy": "spacy",
}
ABBR2MODULE = {v: k for k, v in MODULE2ABBR.items()}
def get_api_doc(api):
    api_docs = api.__doc__
    if api_docs is None:
        return ""
    return api_docs

def get_api_doc_from_module(module_name, api_name):
    module = importlib.import_module(module_name)
    api = getattr(module, api_name)
    return get_api_doc(api)

# np.array
def get_api_doc_from_api_str(api_str):
    module_name, api_name = api_str.split(".")
    if module_name in ABBR2MODULE:
        module_name = ABBR2MODULE[module_name]
    return get_api_doc_from_module(module_name, api_name)

def get_api_doc_from_api_strs(api_strs):
    api_docs = {}
    for api_str in api_strs:
        api_doc = get_api_doc_from_api_str(api_str)
        if api_doc:
            api_docs[api_str] = get_api_doc_from_api_str(api_str)
    return api_docs

def get_all_api_from_module(module_name):
    if module_name in ABBR2MODULE:
        module_name = ABBR2MODULE[module_name]
    module = importlib.import_module(module_name)
    return [api for api in dir(module) if not api.startswith("_")]

def get_api_call_from_module(module_name):
    if module_name in ABBR2MODULE:
        module_name = ABBR2MODULE[module_name]
    module = importlib.import_module(module_name)
    apis = [api for api in dir(module) if not api.startswith("_")]
    api_calls = [module_name + "." + api for api in apis]
    if module_name in MODULE2ABBR:
        abbr_api_calls = [MODULE2ABBR[module_name] + "." + api for api in apis]
    else:
        abbr_api_calls = []
    return api_calls + abbr_api_calls

def append_to_jsonl(data, filename):
    """Append a json payload to the end of a jsonl file."""
    json_string = json.dumps(data)
    if type(filename) == io.StringIO:
        filename.write(json_string + "\n")
    else:
        with open(filename, "a") as f:
            f.write(json_string + "\n")


if __name__ == "__main__":
    # np_array_doc = get_api_doc_from_api_str("np.array")
    # apis = get_api_call_from_module("numpy")
    # print(apis)
    DEFAULT_MODULE = ['numpy', 'pandas']
    apis = []
    for module in DEFAULT_MODULE:
        apis += get_api_call_from_module(module)
    api_docs = get_api_doc_from_api_strs(apis)

    save_dict = {'api': apis, 'doc': api_docs}
    import json
    with open("numpy_pandas_api_doc.json", 'w') as f:
        json.dump(save_dict, f)
    

