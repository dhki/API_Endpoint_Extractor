import json
from utils.android_manifest import extract_permissions_manifest

def analyze_manifest(decoded_dir: str, permission_dict_dir: str, output_dir: str):
    """
    :param decoded_dir: 디컴파일된 APK 디렉토리 경로
    :param permission_dict_dir: 권한 설명이 담긴 JSON 파일
    :param output_dir: analyze_manifest의 출력결과를 json으로 저장할 경로
    :return:
    """
    # 1. 권한 추출
    results = extract_permissions_manifest(decoded_dir, permission_dict_dir)

    # 3. JSON 저장
    with open(output_dir, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"[+] 분석 완료! 결과 저장: {output_dir}")