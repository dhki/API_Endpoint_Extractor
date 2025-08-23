import os
import argparse
import subprocess
import shutil

from utils.result_writer import ResultWriter
from utils.xml_parse import parse_xml_values

DECOMPILED_SMALI_PATH = "./target_smali"

api_endpoints = set()
smali_variables : dict = {}

# decompile apk with apktool
# if apktool is not exist in PATH, error occur.
def decompile_apk(apk_file: str):
    ## find apktool
    if shutil.which('apktool') is None:
        print("[!] Cannot find apktool ... exit ...")
        exit(1)

    ## try decompile
    cmd = ["apktool", "d", apk_file, "-o", DECOMPILED_SMALI_PATH]
    print("[+] Try decompile apk ...")
    print(f"    command: ", " ".join(cmd))

    try:
        subprocess.run(cmd, shell=True)

        print("[+] Decompile completed")
    except Exception as e:
        print("[!] Error occured")
        print(f"    {e}")


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('apk_path', type=str, help='path of target apk file')
    parser.add_argument("-o", "--output_file", type=str, default=None)
    args = parser.parse_args()

    result_writer = ResultWriter(path=args.output_file)

    # decompile apk
    decompile_apk(apk_file=args.apk_path)

    # parse strings.xml
    xml_urls = parse_xml_values(f"{DECOMPILED_SMALI_PATH}/res/values/strings.xml")
    for url in xml_urls:
        api_endpoints.add(url)
    
    # make result file (or print at console)
    for v in api_endpoints:
        result_writer.write(v)
    result_writer.close()

if __name__ == "__main__":
    main()