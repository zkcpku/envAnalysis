from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from autocomplete import extract_symbols
tokenizer = None
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
            symbol_dict[e[0]] = {"type": k, "code": e[1][0], "pos": e[1][1]}
    rst = { "symbols": symbol_dict, "content": each_content}
    return rst

def codeContext2jsonContext(each_content):
    api_calls, suggestions = extract_symbols(each_content)
    suggestions, suggestion_loc = format_symbol_suggestion(suggestions)
    symbol_dict = {}
    for k in suggestion_loc:
        if k not in ['mannual_defined_function', 'mannual_defined_class']:
            continue
        for e in suggestion_loc[k]:
            symbol_dict[e[0]] = {"type": k, "code_body": e[1][0], "pos": e[1][1]}
    # rst = { "symbols": symbol_dict, "content": each_content}
    # json_context = [{"entity_name": "", "entity_body": ""}]
    json_context = []
    for k in suggestion_loc:
        if k in ['mannual_defined_function', 'mannual_defined_class']:
            for e in suggestion_loc[k]:
                json_context.append({"entity_name": e[0], "entity_body": e[1][0]})
    return json_context

def extract_files(inp_dir, file_type=".py"):
    import os
    files = []
    for root, dirs, fs in os.walk(inp_dir):
        for f in fs:
            if f.endswith(file_type):
                files.append(os.path.join(root, f))
    return files


# Given a file
# Return a list of dict:
# {'symbol', 'type', 'location', 'content'}
def tokenizer_len(text, tokenizer):
    return len(tokenizer(text, padding=False).input_ids)
def tokenizer_lens(texts, tokenizer):
    lens = tokenizer(texts, padding=False).input_ids
    return [len(e) for e in lens]
def file2symbols(file_path, tokenizer_path):
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    FILTER_TYPE = ['mannual_defined_function', 'mannual_defined_class']
    with open(file_path, 'r') as f:
        text = f.read()
    all_symbols = extract(text)
    rst = []
    need_tokenizer = []
    for k in all_symbols['symbols']:
        symbol = k
        type = all_symbols['symbols'][k]['type']
        location = all_symbols['symbols'][k]['pos']
        # location = tokenizer_len(text[:location], tokenizer)
        need_tokenizer.append(text[:location])
        content = all_symbols['symbols'][k]['code']
        # rst.append({'symbol': symbol, 'type': type, 'location': location, 'content': content})
        rst.append({'symbol': symbol, 'type': type, 'byte_location': location})
    lens = tokenizer_lens(need_tokenizer, tokenizer)
    for i in range(len(rst)):
        # rst[i]['location'] = sum(lens[:i+1])
        rst[i]['location'] = lens[i]
    rst = [e for e in rst if e['type'] in FILTER_TYPE]
    return rst


# time
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

# 这将告诉alarm在多少秒后引发一个signal.SIGALRM信号
signal.signal(signal.SIGALRM, timeout_handler)

def project2symbols(inp_dir, tokenizer_path):
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    # return: [{"input", "output", "metadata"}]
    # metadata: {"file_path", "file_length", "symbol_dict"}
    rtn = []
    files = extract_files(inp_dir, file_type=".py")
    print("total files: ", len(files))
    for f in tqdm(files, ncols=0):
        signal.alarm(20)  # 设置5秒的时间限制
        try:
            with open(f, 'r') as open_f:
                text = open_f.read()
            this_inp = text
            this_file_length = tokenizer_len(this_inp, tokenizer)
            this_symbol_dict = file2symbols(f, tokenizer_path)
            this_output = [e['symbol'] for e in this_symbol_dict]
            this_metadata = {"file_path": f, "file_length": this_file_length, "symbol_dict": this_symbol_dict}
            rtn.append({"input": this_inp, "output": this_output, "metadata": this_metadata})
        except TimeoutException:
            print("Time's up for file: ", f)
        except Exception as e:
            print("error: ", f, e)
        finally:
            # 确保清除了定时器，防止影响到下一次循环
            signal.alarm(0)
    return rtn

def drawfig_filelength_symbolnum(project2symbols_rst, title=""):
    import matplotlib.pyplot as plt
    project2symbols_rst = [e for e in project2symbols_rst if e['metadata']['file_length'] > 10000 and e['metadata']['file_length'] < 16000 and len(e['metadata']['symbol_dict']) > 10]
    print("file_path: ", [e['metadata']['file_path'] for e in project2symbols_rst])
    file_length = [e['metadata']['file_length'] for e in project2symbols_rst]
    symbol_num = [len(e['metadata']['symbol_dict']) for e in project2symbols_rst]
    # draw two figures
    # the first figure is the file length and symbol number
    # the second figure is the distribution of symbol position
    plt.figure()
    plt.scatter(file_length, symbol_num)
    plt.xlabel("file length")
    plt.ylabel("symbol number")
    plt.title("file length and symbol number" + "|" + title)
    plt.show()
    # the second figure
    plt.figure()
    all_symbol_pos = []
    for e in project2symbols_rst:
        symbol_dict = e['metadata']['symbol_dict']
        symbol_pos = [symbol_dict[i]['location'] for i in range(len(symbol_dict))]
        all_symbol_pos += symbol_pos
    plt.hist(all_symbol_pos, bins=20, alpha=0.5)
    plt.xlabel("symbol position")
    plt.ylabel("symbol number")
    plt.title("symbol position distribution" + "|" + title)
    plt.show()
    return None

def filter_project2symbols(project2symbols_rst, file_length_range=[10000, 16000], symbol_num_range=[10, 10000000]):
    return [e for e in project2symbols_rst if e['metadata']['file_length'] > file_length_range[0] and e['metadata']['file_length'] < file_length_range[1] and len(e['metadata']['symbol_dict']) > symbol_num_range[0] and len(e['metadata']['symbol_dict']) < symbol_num_range[1]]

class TestCase:
    def _test_extract():
        with open("code_example.py",'r') as f:
            content = f.read()
            rst = extract(content)
        # print(rst['symbols'].keys())
        # print(rst['symbols'])
        mannual_defined_funcs = [e for e in rst['symbols'] if "mannual_defined_function" in rst['symbols'][e]['type'] ]
        print(mannual_defined_funcs)
        mannual_defined_cls = [e for e in rst['symbols'] if "mannual_defined_class" in rst['symbols'][e]['type'] ]
        print(mannual_defined_cls)
    def _test_file2symbols():
        inp_file = "code_example.py"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        rst = file2symbols(inp_file, tokenizer_path)
        print(rst)
        tmp_tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        with open(inp_file, 'r') as f:
            text = f.read()
        input_ids = tokenizer([text], return_tensors='pt').input_ids
        # decode after 203
        # print(input_ids[0][203:])
        # print(tmp_tokenizer.decode(input_ids[0][203:203+20]))
    def _test_project2symbols():
        inp_dir = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/langchain-master"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        rst = project2symbols(inp_dir, tokenizer_path)
        import json
        out_path = inp_dir + "/symbols.json"
        with open(out_path, 'w') as f:
            json.dump(rst, f)
        drawfig_filelength_symbolnum(rst)
    def _test_drawfig_filelength_symbolnum():
        import json
        inp_json = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/langchain-master/symbols.json"
        with open(inp_json, 'r') as f:
            rst = json.load(f)
        drawfig_filelength_symbolnum(rst)
    def _test_multiple_projects():
        inp_base = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        # ["langchain-master", "numpy-main", "tensorflow-master", "langchain-master", "numpyml-master", "gradio-main", "pytorch-main"
        for each_project in ["transformers-main", "accelerate-main", "datasets-main","diffusers-main", "optimum-main" ,"peft-main"]:
            print("running ", each_project, " ...")
            inp_dir = inp_base + each_project
            rst = project2symbols(inp_dir, tokenizer_path)
            import json
            out_path = inp_dir + "/symbols.json"
            with open(out_path, 'w') as f:
                json.dump(rst, f)
    def _test_drawfig_multiprojects():
        inp_base = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        dir_list = ["transformers-main", "accelerate-main", "datasets-main","diffusers-main", "optimum-main" ,"peft-main"]
        json_file = "symbols.json"
        import json
        for each_project in dir_list:
            inp_dir = inp_base + each_project
            inp_json = inp_dir + "/" + json_file
            with open(inp_json, 'r') as f:
                rst = json.load(f)
            drawfig_filelength_symbolnum(rst, title=each_project)
    def _test_filter_project2symbols():
        inp_base = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        dir_list = ["langchain-master", "numpy-main", "tensorflow-master", "numpyml-master", "gradio-main"] + ["transformers-main", "accelerate-main", "datasets-main","diffusers-main", "optimum-main" ,"peft-main"]
        json_file = "symbols.json"
        import json
        count_length = {}
        total_rst = []
        for each_project in dir_list:
            inp_dir = inp_base + each_project
            inp_json = inp_dir + "/" + json_file
            with open(inp_json, 'r') as f:
                rst = json.load(f)
            l_range = [10000, 16000]
            s_range = [10, 10000000]
            rst = filter_project2symbols(rst, file_length_range=l_range, symbol_num_range=s_range)
            total_rst += rst
            count_length[each_project] = len(rst)
            save_file = "symbols_filtered" + "-".join([str(e) for e in l_range]) + "-".join([str(e) for e in s_range]) + ".json"
            with open(inp_dir + save_file, 'w') as f:
                json.dump(rst, f)
        for k in count_length:
            print(k, count_length[k])
        sum_count_length = sum([count_length[k] for k in count_length])
        print("total: ", sum_count_length)
        for e in total_rst:
            e['metadata']['file_path'] = e['metadata']['file_path'].split("ROPE/dataset/")[-1]
            # remove personal information
        with open("/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/symbols_filtered.json", 'w') as f:
            json.dump(total_rst, f)
        print("length of total_rst: ", len(total_rst))
    def _test_renew_dataset():
        import json
        inp_path = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/openai_src/gen_out/openai_default_codesymbols.jsonl"
        tokenizer_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/Llama-2-7b-hf'
        with open(inp_path,'r') as f:
            lines = f.readlines()
            lines = [json.loads(x) for x in lines]
        save_lines = []
        for each_line in tqdm(lines):
            metadata = each_line['metadata']
            file_path = metadata['file_path']
            file_path = "/Users/zkcpku/Documents/seke/mywork/分块ROPE/dataset/" + file_path
            this_symbol_dict = file2symbols(file_path, tokenizer_path)
            each_line['metadata']['symbol_dict'] = this_symbol_dict
            save_lines.append(each_line)
        save_path = inp_path + ".renew"
        with open(save_path, 'w') as f:
            for e in save_lines:
                f.write(json.dumps(e) + "\n")
    def test_gen_json_format_context():
        import json
        inp_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/openai_src/codesymbols_outputless100.jsonl'
        out_path = '/Users/zkcpku/Documents/seke/mywork/分块ROPE/openai_src/codesymbols_outputless100.jsoncontext.jsonl'
        out_lines = []
        with open(inp_path, 'r') as f:
            lines = f.readlines()
            lines = [json.loads(x) for x in lines]
        for each_line in tqdm(lines):
            each_inp = each_line['input']
            json_context = codeContext2jsonContext(each_inp)
            each_line['json_context'] = json_context
            out_lines.append(each_line)
        with open(out_path, 'w') as f:
            for e in out_lines:
                f.write(json.dumps(e) + "\n")
        

            
            
            


    



if __name__ == "__main__":
    # test all functions defined in TestCase
    t = TestCase()
    for k in dir(t):
        if k.startswith("test_"):
            print("running ", k, " ...")
            method_to_call = getattr(TestCase, k)
            method_to_call()



    