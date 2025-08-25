import os
import re

INS_ASSIGN = "const-string"
INS_INVOKE_D = "invoke-direct"
INS_INVOKE_V = "invoke-virtual"

STRING_BUILDER_INIT = "Ljava/lang/StringBuilder;-><init>"
STRING_BUILDER_APPEND = "Ljava/lang/StringBuilder;->append"
STRING_BUILDER_TOSTRING = "Ljava/lang/StringBuilder;->toString"

RETROFIT_BUILDER_BASE = "Lretrofit2/Retrofit$Builder;->baseUrl"
RETROFIT_BUILDER_CREATE = "Lretrofit2/Retrofit;->create"

smali_variables = {}
url_endpoints = set()

# 'parse_all_smali' parse all smali files under parameter dir(path)
# parse all files and track all strings
# then, check if the strings are URL Endpoint or not 
def parse_all_smali(dir: str):
    global smali_variables, url_endpoints
    print("=" * 50)
    print(f"{'Parsing all smali file...'.center(50)}")
    print("-" * 50)
    prev_len = 0

    for root, _, files in os.walk(dir):
        for file in files:
            print(f"\r\t{' ' * prev_len}", end="")
            print(f"\r\t{file.ljust(64)}", end="")
            prev_len = len(file)

            smali_variables = {}

            if file.endswith(".smali"):
                
                ## if smali file has retrofit format, consider it has only retrofit paths
                ## so, TODO: store the retrofit paths
                if check_retrofit_format(file):
                    break
                
                
                with open(f"{root}/{file}", "r") as f:
                    contents = f.readlines()

                    for l in contents:
                        try:
                            instructions = parse_smali_line(l)
                            if instructions is None:
                                continue
                            
                            if instructions['ins'] == INS_ASSIGN:
                                smali_variables[instructions['var'][0]] = instructions['val'].replace('"', '')
                                if smali_variables[instructions['var'][0]].startswith(("http://", "https://")) and smali_variables[instructions['var'][0]] not in url_endpoints:
                                    url_endpoints.add(smali_variables[instructions['var'][0]])
                                    print(f"\r\t{' ' * prev_len}", end="")
                                    print(f"\r{smali_variables[instructions['var'][0]]}")

                            elif instructions['ins'] == INS_INVOKE_D:
                                if STRING_BUILDER_INIT in instructions['val']:
                                    if len(instructions['var']) > 1:
                                        smali_variables[instructions['var'][0]] = smali_variables.get(instructions['var'][1], "****")
                                    else:
                                        smali_variables[instructions['var'][0]] = ""
                            
                            elif instructions['ins'] == INS_INVOKE_V:
                                if STRING_BUILDER_APPEND in instructions['val']:
                                    for i in range(1, len(instructions['var'])):
                                        smali_variables[instructions['var'][0]] = smali_variables.get(instructions['var'][0], "****") + smali_variables.get(instructions['var'][i], "****")
                                        if smali_variables[instructions['var'][0]].startswith(("http://", "https://")) and smali_variables[instructions['var'][0]] not in url_endpoints:
                                            url_endpoints.add(smali_variables[instructions['var'][0]])
                                            print(f"\r\t{' ' * prev_len}", end="")
                                            print(f"\r{smali_variables[instructions['var'][0]]}")
                        except Exception as e:
                            pass

    print(f"\r\t{' ' * prev_len}", end="")
    print(f"\r{'=' * 50}")
    return url_endpoints



# this function checks if the file has retrofit format
# TODO: checks with regular expressions, return true or false
def check_retrofit_format(file_path: str):
    return False


# TODO: parse smali line
# and return instructions, variable, function names, etc.
def parse_smali_line(line: str) -> dict:
    
    parts = line.strip().split()
    if parts:
        if parts[0] not in [INS_ASSIGN, INS_INVOKE_D, INS_INVOKE_V]:
            return None
        
        instructions = {
            'ins' :  parts[0],
            'var' :  re.findall(r'[vp]\d+', line),
            'val' :  parts[-1],
        }

        return instructions
    else:
        return None
