from autocomplete import Autocomplete, PY_LANGUAGE, Parser
import sys
import os
import json
import argparse
from tqdm import tqdm
from extract_api_doc import *

def count_jsonl(filename):
    with open(filename, 'r') as f:
        count = 0
        for line in f:
            count += 1
    return count

def read_jsonl(filename):
    with open(filename, 'r') as f:
        for line in f:
            yield json.loads(line)
def write_jsonl(filename, data):
    with open(filename, 'w') as f:
        for line in data:
            f.write(json.dumps(line) + '\n')
def write_jsonl_append(filename, each_data):
    with open(filename, 'a+') as f:
        f.write(json.dumps(each_data) + '\n')

def extract_surronding_linenums(code, line_num, surround_line_num=3):
    lines = code.split("\n")
    start_line = max(0, line_num - surround_line_num)
    end_line = min(len(lines), line_num + surround_line_num)
    return start_line, end_line
    # return "\n".join(lines[start_line:end_line])

def compose_start_and_end_line(start_end_pairs):
    start_end_pairs = sorted(start_end_pairs, key=lambda x:x[0])
    new_start_end_pairs = []
    this_start, this_end = -1, -1
    for start, end in start_end_pairs:
        if start >= this_start and start <= this_end:
            last_pair = new_start_end_pairs[-1]
            new_start_end_pairs[-1] = [last_pair[0], end]
            this_start, this_end = last_pair[0], end
        else:
            new_start_end_pairs.append([start, end])
            this_start, this_end = start, end
    return new_start_end_pairs

def remove_tab_or_space(code):
    code_lines = code.split('\n')
    prefix_tab_or_space = []
    for line in code_lines:
        if line.strip() == '':
            prefix_tab_or_space.append(None)
        else:
            prefix_tab_or_space.append(len(line) - len(line.lstrip()))
    valid_prefix = [e for e in prefix_tab_or_space if e is not None]
    if len(valid_prefix) != 0:
        minimal_prefix = min([e for e in prefix_tab_or_space if e is not None])
    else:
        minimal_prefix = 0

    code_lines = [line[minimal_prefix:] for line in code_lines]
    # remove #
    code_lines = [line for line in code_lines if not line.lstrip().startswith('#') and line.strip() != '']
    return '\n'.join(code_lines)



def extract_code_lines(code, start_end_pairs):
    code_lines = code.split('\n')
    ret_codes = []
    for start_line,end_line in start_end_pairs:
        this_code = "\n".join(code_lines[start_line:end_line])
        ret_codes.append({
            'func_code_string': remove_tab_or_space(this_code),
            'line_nums': [start_line,end_line]
            })
    return ret_codes

def str2bool(str):
    return True if str.lower() == 'true' else False


def main():
    parser = argparse.ArgumentParser(description="Extract utility")
    parser.add_argument(
        '--file',
        dest='file',
        type=str,
        help='The file path to source code.',
        required=True)
    parser.add_argument(
        '--key',
        dest='key',
        type=str,
        help='The json key for the source code.',
        required=True)
    parser.add_argument(
        '--save_file',
        dest='save_file',
        type=str,
        help='The file path to save the extracted api calls.',
        required=True)
    parser.add_argument(
        '--extract_surrounding_code',
        dest='extract_surrounding_code',
        type=str2bool,
        help='Whether to extract surrounding code.',
        default=True)
    args = parser.parse_args()
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    extract_surrounding_code = args.extract_surrounding_code
    import ipdb; ipdb.set_trace()

    json_reader = read_jsonl(args.file)

    DEFAULT_MODULE = ['numpy', 'pandas']
    apis = []
    for module in DEFAULT_MODULE:
        apis += get_api_call_from_module(module)

    def api_in_apis(search_api, apis):
        for api in apis:
            if api in search_api:
                return True
        return False

    no_valid = 0
    total_num = 0
    for json_obj in tqdm(json_reader, total=count_jsonl(args.file)):
        code = json_obj[args.key]
        # print(code)
        code = bytes(code, "utf-8")
        tree = parser.parse(code)
        completer = Autocomplete(tree, code, len(code))
        api_calls = completer.extract_used_api()
        json_obj['api_calls'] = api_calls
        json_obj['valid_api_calls'] = [api_pair for api_pair in api_calls if api_in_apis(api_pair[0], apis)]
        if len(json_obj['valid_api_calls']) == 0:
            no_valid += 1
            continue
        if extract_surrounding_code:
            all_line_nums = [e[-1] for e in json_obj['valid_api_calls']]
            start_end_pairs = [extract_surronding_linenums(json_obj[args.key],linen,5) for linen in all_line_nums]
            start_end_pairs = compose_start_and_end_line(start_end_pairs)
            surround_codes = extract_code_lines(json_obj[args.key], start_end_pairs)
            for each_surround_code in surround_codes:
                total_num += 1
                # import ipdb; ipdb.set_trace()
                write_jsonl_append(args.save_file,each_surround_code)
        else:
            total_num += 1
            write_jsonl_append(args.save_file, json_obj)


            
        # print(json_obj)

        # write_jsonl_append(args.save_file, json_obj)
        # print("\n")
        # print(api_calls)
        # break
    print("no_valid:", no_valid)
    print("total_num:", total_num)



if __name__ == "__main__":
    main()
    # python extract_csn_python_api.py --file "/Users/zkcpku/Documents/seke/pretrain/envAnalysis/data/CSN_python_func_code_string_filter(numpy&pandas).json" --key func_code_string --save_file "/Users/zkcpku/Documents/seke/pretrain/envAnalysis/data/CSN_python_func_code_string_filter_np&pd_with_valid_api.surround.json"