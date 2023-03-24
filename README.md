# treesitter-autocomplete
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
