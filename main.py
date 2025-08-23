import os
import argparse
import subprocess
import shutil
import json

from utils.result_writer import ResultWriter
from utils.xml_parse import parse_xml_values
from utils.android_manifest import parse_permissions_manifest

DECOMPILED_SMALI_PATH = "./target_smali"
ANDROID_MANIFEST_PATH = "./outputs/apk_permissions.json"
AM_PERMISSION_DICT_PATH = "./resources/user_permission.json"

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

def analyze_manifest(decoded_dir: str, permission_dict_dir: str, output_dir: str):
    """
    :param decoded_dir: 디컴파일된 APK 디렉토리 경로
    :param permission_dict_dir: 권한 설명이 담긴 JSON 파일
    :param output_dir: analyze_manifest의 출력결과를 json으로 저장할 경로
    :return:
    """
    # 1. 권한 추출
    results = parse_permissions_manifest(decoded_dir, permission_dict_dir)

    # 3. JSON 저장
    with open(output_dir, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"[+] Permission anlaysis done! stored at :{output_dir}")


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('apk_path', type=str, help='path of target apk file')
    parser.add_argument("-o", "--output_file", type=str, default=None)
    args = parser.parse_args()

    result_writer = ResultWriter(path=args.output_file)

    # decompile apk
    decompile_apk(apk_file=args.apk_path)

    # Android Manifest 분석
    os.makedirs(os.path.dirname(ANDROID_MANIFEST_PATH), exist_ok=True)
    analyze_manifest(DECOMPILED_SMALI_PATH, AM_PERMISSION_DICT_PATH, ANDROID_MANIFEST_PATH)

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
