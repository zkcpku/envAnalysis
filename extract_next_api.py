# %%
import os
import json
import sys
from autocomplete import Autocomplete, PY_LANGUAGE, Parser
import argparse
from tqdm import tqdm
from extract_api_doc import *
from extract_csn_python_api import count_jsonl, read_jsonl, write_jsonl, write_jsonl_append
import functools

inp_path = "/Users/zkcpku/Documents/seke/mywork/dependency/cloudbrain/dataset/CSN_valid_np_pd328.only_search.jsonl"
output_path = "/Users/zkcpku/Documents/seke/mywork/dependency/cloudbrain/dataset/CSN_valid_np_pd328.with_rst.jsonl"
parser = Parser()
parser.set_language(PY_LANGUAGE)


# %%
def get_apiend_pos(APISearch_pos, code_string):
    APISearch_end_pos = APISearch_pos[2]
    apiend_pos = code_string[APISearch_end_pos:].find("*/")
    if apiend_pos == -1:
        assert False
        return None
    apiend_pos += APISearch_end_pos
    return apiend_pos

# %%
def string_find_all(code_string, s):
    pos = 0
    pos_list = []
    while True:
        pos = code_string.find(s, pos)
        if pos == -1:
            break
        pos_list.append(pos)
        pos += len(s)
    return pos_list
def add_apisearch_rst(code_string):
    # code_string = code_string.replace("*/","*/ ")
    code = bytes(code_string, "utf-8")
    tree = parser.parse(code)
    completer = Autocomplete(tree, code, len(code))
    api_calls = completer.extract_used_api()
    api_end_pos = string_find_all(code_string, "*/")
    api_calls = sorted(api_calls, key=lambda x:x[2])

    def get_close_api_for_each(api_end_poses, extract_apies):
        close_api_for_each = []
        for i in range(len(api_end_poses)):
            this_close_api = "None"
            for j in range(len(extract_apies)):
                if api_end_poses[i] < extract_apies[j][2]:
                    this_close_api = extract_apies[j][0]
                    break
            close_api_for_each.append(this_close_api)
        return close_api_for_each
    def clean_close_api(origin_api):
        # if "(" in origin_api:
        #     origin_api = origin_api.split("(")[0]
        return origin_api
    # print(api_calls)
    SearchRst_apis = get_close_api_for_each(api_end_pos, api_calls)
    SearchRst_apis = [clean_close_api(e) for e in SearchRst_apis]
    
    def add_into_code_string(code_string, api_end_pos, SearchRst_apis):
        split_code_string_pos = api_end_pos
        split_code_string_pos.append(len(code_string))
        split_code_string = []
        for i in range(len(split_code_string_pos)):
            if i == 0:
                split_code_string.append(code_string[:split_code_string_pos[i]])
            else:
                split_code_string.append(code_string[split_code_string_pos[i-1]:split_code_string_pos[i]])
        new_code_string = ""
        for i in range(len(split_code_string)):
            new_code_string += split_code_string[i]
            if i < len(split_code_string) - 1:
                new_code_string += f"->{SearchRst_apis[i]}"
        return new_code_string
    return add_into_code_string(code_string, api_end_pos, SearchRst_apis)

# %%
inp_data = read_jsonl(inp_path)
for each_obj in tqdm(inp_data):
    each_obj["without_rst"] = each_obj['func_code_string']
    each_obj['func_code_string'] = add_apisearch_rst(each_obj['func_code_string'])
    write_jsonl_append(output_path, each_obj)

# %%



