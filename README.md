# treesitter-autocomplete-&-extract_api

## treesitter-extract_api
Extract API from python code using tree-sitter

### Example Run Commands

捕获api所在行的上下几行的代码
```Shell
python extract_csn_python_api.py --file "envAnalysis/data/CSN_python_func_code_string_filter(numpy&pandas).json" --key func_code_string --save_file "envAnalysis/data/CSN_python_func_code_string_filter_np&pd_with_valid_api.json"
```

如果需要捕获所有代码
```Shell
python extract_csn_python_api.py --file "envAnalysis/data/CSN_python_func_code_string_filter(numpy&pandas).json" --key func_code_string --save_file "envAnalysis/data/CSN_python_func_code_string_filter_np&pd_with_valid_api.json" --extract_surrounding_code False
```


## treesitter-autocomplete
Autocomplete utility using tree-sitter for python code

### Requirements
Vendor packages have been prebuilt into `build/languages.so` by `build_tspy_library.py`
```Shell
pip install tree-sitter
```

### Example Run Commands
```Shell
python autocomplete.py --file code_example.py --pos 19
python autocomplete.py --file code_example.py --pos 18
python autocomplete.py --file code_example.py --pos 6
python autocomplete.py --file code_example.py --pos 20
python autocomplete.py --file code_example.py --pos 1000
```
