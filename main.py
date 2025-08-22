import argparse
import subprocess
import shutil

from utils.result_writer import ResultWriter

DECOMPILED_SMALI_PATH = "./target_smali"

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
    args = parser.parse_args()

    # decompile apk
    decompile_apk(apk_file=args.apk_path)

    ## TODO: Find API Endpoint

if __name__ == "__main__":
    main()