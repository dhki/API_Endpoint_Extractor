import os
import json
import xml.etree.ElementTree as ET
import re

def clean_text(s: str) -> str:
    """
    보이지 않는 제어 문자 및 surrogate 문자 제거

    :param s: string
    :return: 불필요한 문자가 제거된 string
    """
    # surrogate 문자 제거 → 공백
    s = re.sub(r'[\uD800-\uDFFF]', ' ', s)
    # 제어 문자 제거 → 공백 (tab/newline 제외)
    s = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', ' ', s)
    return s

def find_manifest_files(directory: str):
    """
    디컴파일된 디렉토리에서, AndroidManifest 파일의 경로 리스트를 추출
    
    :param directory: 디컴파일된 directory 경로
    :return: AndroidManifest.xml 파일 경로 리스트
    """
    manifest_files = []
    for root_dir, _, files in os.walk(directory):
        if "AndroidManifest.xml" in files:
            manifest_files.append(os.path.join(root_dir, "AndroidManifest.xml"))
    manifest_files.sort()
    return manifest_files

def load_permissions_dict(json_file_path: str) -> dict:
    """
    JSON 파일을 열어 파이썬 dict로 변환하고 제어 문자 제거

    :param json_file_path: user_permission.json 파일의 경로
    :return: 파이썬 딕셔너리
    """
    """JSON 파일을 열어 파이썬 dict로 변환하고 제어 문자 제거"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        raw_dict = json.load(f)
    # 모든 description에 clean_text 적용
    return {k: clean_text(v) for k, v in raw_dict.items()}

def parse_manifest(file_path: str, permissions_dict: dict):
    """
    AndroidManifest.xml에서 패키지명과 권한 추출

    :param file_path: AndroidManifest.xml 경로
    :param permissions_dict: 권한 설명 dict
    :return: (package_name, permissions_list, file_path)
    """
    package_name = "Unknown Package"
    extracted_permissions = []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        package_name = root.get("package", "Unknown Package")

        ns = {'android': 'http://schemas.android.com/apk/res/android'}
        for perm in root.findall("uses-permission"):
            perm_name = perm.get(f"{{{ns['android']}}}name")
            if perm_name:
                simple_name = perm_name.split('.')[-1]  # android.permission.CAMERA -> CAMERA
                raw_description = permissions_dict.get(simple_name, "No description available")
                description = clean_text(raw_description)  # 제어 문자 제거
                extracted_permissions.append({
                    "permission": simple_name,
                    "description": description
                })

    except (ET.ParseError, FileNotFoundError, PermissionError) as e:
        # 예외 발생 시 기본값 반환
        extracted_permissions = []

    # Windows/Unix 경로 혼합 문제 해결
    return package_name, extracted_permissions, os.path.normpath(file_path)

def extract_permissions_manifest(decoded_dir: str, permission_dict_path: str) -> dict:
    """
    디컴파일된 APK 디렉토리에서 AndroidManifest.xml을 파싱하고 권한 정보를 추출(controller)

    :param decoded_dir: 디컴파일된 APK 디렉토리 경로
    :param permission_dict_path: 권한 설명이 담긴 JSON 파일
    :return: {패키지명: {"file_path": str, "permissions": list}} 형태의 딕셔너리
    """

    # Manifest 파일 찾기
    manifest_files = find_manifest_files(decoded_dir)

    # 권한 딕셔너리 로드
    permissions_dict = load_permissions_dict(permission_dict_path)

    results = {}
    for mf in manifest_files:
        package, permissions, path = parse_manifest(mf, permissions_dict)
        results[package] = {
            "file_path": path,
            "permissions": permissions
        }

    # 2. 콘솔 출력
    print("[+] Permission 추출 완료")
    for package_name, info in results.items():
        permissions = info.get("permissions", [])
        if not permissions:
            continue  # 권한이 없는 패키지는 출력하지 않음

        print("="*50)
        print(f"패키지: {package_name}")
        print(f"Manifest 파일: {info.get('file_path')}")
        print("-"*50)
        print("권한 목록:")
        for perm in permissions:
            print(f"  - {perm['permission']}: {perm['description']}")
        print("="*50)

    return results