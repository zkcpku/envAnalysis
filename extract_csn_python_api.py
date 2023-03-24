from autocomplete import Autocomplete, PY_LANGUAGE, Parser
import sys
import os
import json
import argparse
from tqdm import tqdm

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
    args = parser.parse_args()
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    json_reader = read_jsonl(args.file)
    for json_obj in tqdm(json_reader, total=count_jsonl(args.file)):
        code = json_obj[args.key]
        # print(code)
        code = bytes(code, "utf-8")
        tree = parser.parse(code)
        completer = Autocomplete(tree, code, len(code))
        api_calls = completer.extract_used_api()
        json_obj['api_calls'] = api_calls
        # print(json_obj)
        write_jsonl_append(args.save_file, json_obj)
        # print("\n")
        # print(api_calls)
        # break



if __name__ == "__main__":
    main()