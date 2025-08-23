import argparse
import subprocess
import shutil
import os

from utils.result_writer import ResultWriter
from controller.controller import analyze_manifest

DECOMPILED_SMALI_PATH = "./target_smali"
ANDROID_MANIFEST_PATH = "./outputs/android_manifest_output.json"
AM_PERMISSION_DICT_PATH = "./resources/user_permission.json"

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

    # ----------------------------
    # 디컴파일 옵션 그룹
    # ----------------------------
    decompile_group = parser.add_argument_group("Decompile Options")
    decompile_group.add_argument("-d", "--decompile", action="store_true", help="APK 디컴파일 실행")
    parser.add_argument('--apk_path', type=str, help='path of target apk file')

    # ----------------------------
    # AndroidManifest 분석 옵션 그룹
    # ----------------------------
    manifest_group = parser.add_argument_group("Manifest Analyze Options")
    manifest_group.add_argument("-am", "--analyze_manifest", action="store_true", help="AndroidManifest.xml 분석 실행")

    # ----------------------------
    # 인자 파싱 및 기능 실행
    # ----------------------------
    args = parser.parse_args()

    # 1. 디컴파일
    if args.decompile:
        if not args.apk_path:
            parser.error("--apk_path 가 필요합니다 (예: python main.py -d --apk_path app.apk)")
        decompile_apk(apk_file=args.apk_path)

    # 2. AndroidManifest 분석
    elif args.analyze_manifest:
        os.makedirs(os.path.dirname(ANDROID_MANIFEST_PATH), exist_ok=True)
        analyze_manifest(DECOMPILED_SMALI_PATH, AM_PERMISSION_DICT_PATH, ANDROID_MANIFEST_PATH)

    ## TODO: 나머지 명령어들도 이곳에 추가
    ## TODO: Find API Endpoint

    # 아무 옵션도 없으면 도움말 출력
    else:
        parser.print_help()


if __name__ == "__main__":
    main()