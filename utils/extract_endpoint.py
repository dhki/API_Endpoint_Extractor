#!/usr/bin/env python3
# extract_endpoint.py
import os
import re
import json
import base64
import argparse
from collections import namedtuple

# patterns.py에서 정의된 정규식 및 상수들
from patterns import (
    URL_REGEX, HOST_REGEX, CONST_STRING, BASE64_LIKE, SIGNS, DEFAULT_EXTS, FIELD_STRING
)
from result_writer import ResultWriter

Finding = namedtuple('Finding', 'value file line kind score context')


# ---------- 파일 순회 ----------
def walk_files(root, exts=DEFAULT_EXTS):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(exts):
                yield os.path.join(dirpath, fn)


# ---------- 스코어링/문맥 ----------
'''
    스코어링 기준 예시:
    - URL 직접 매칭: 80점
    - 호스트 매칭: 40점
    - 디코딩된 URL: 90점
    - 디코딩된 호스트: 60점
    - retrofit @GET 등 인자: 95점
    - 시그니처 인접: +10점
    - 기타: 10점
'''

def score_of(kind, near_sign=False):
    base = {
        'url': 80,
        'host': 40,
        'decoded-url': 90,
        'decoded-host': 60,
        'retrofit-arg': 95,
    }.get(kind, 10)
    return base + (10 if near_sign else 0)


def near_signature(lines, idx, window=12):
    s = '\n'.join(lines[max(0, idx - window): idx + window + 1])
    return any(p.search(s) for p in SIGNS)


# ---------- 디코딩/복원 ----------
def decode_base64(s):
    try:
        b = base64.b64decode(s)
        text = b.decode('utf-8', errors='ignore')
        if URL_REGEX.search(text) or HOST_REGEX.search(text):
            return text
    except Exception:
        pass
    return None


def try_reconstruct_simple_concat(lines, idx):
    """
    단순 문자열 결합 패턴(예: concat, StringBuilder append 체인)에서
    주변 const-string 상수들을 긁어 이어붙이는 best-effort 복원.
    """
    window = lines[max(0, idx - 8): idx + 8]
    joined = '\n'.join(window)
    consts = CONST_STRING.findall(joined)
    if len(consts) >= 2:
        return ''.join(consts)
    return None


# ---------- 핵심 추출 ----------
def extract_from_file(path):
    findings = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        # 1) 직접 URL 매칭
        for m in URL_REGEX.finditer(line):
            val = m.group(0)
            findings.append(Finding(
                val, path, i + 1, 'url',
                score_of('url', near_signature(lines, i)),
                line.strip()
            ))

        # 2) 스킴 없는 호스트 매칭
        for m in HOST_REGEX.finditer(line):
            val = m.group(1)
            findings.append(Finding(
                val, path, i + 1, 'host',
                score_of('host', near_signature(lines, i)),
                line.strip()
            ))

        # 3) const-string -> base64 디코딩 + 문자열 결합 복원
        cm = CONST_STRING.match(line)
        if cm:
            s = cm.group(1)
            # base64 후보 디코딩
            if BASE64_LIKE.match(s):
                decoded = decode_base64(s)
                if decoded:
                    for m in URL_REGEX.finditer(decoded):
                        findings.append(Finding(
                            m.group(0), path, i + 1, 'decoded-url',
                            score_of('decoded-url'),
                            f'base64:{s[:16]}...'
                        ))
                    for m in HOST_REGEX.finditer(decoded):
                        findings.append(Finding(
                            m.group(1), path, i + 1, 'decoded-host',
                            score_of('decoded-host'),
                            f'base64:{s[:16]}...'
                        ))
        
            # 단순 결합 복원
            recon = try_reconstruct_simple_concat(lines, i)
            if recon:
                for m in URL_REGEX.finditer(recon):
                    findings.append(Finding(
                        m.group(0), path, i + 1, 'url',
                        score_of('url', near_signature(lines, i)),
                        'reconstruct'
                    ))

        # 4) .field 문자열 상수 추출
        fm = FIELD_STRING.match(line)
        if fm:
            s = fm.group(1)

            # 4-1) .field 직접 URL/호스트
            for m in URL_REGEX.finditer(s):
                findings.append(Finding(
                    m.group(0), path, i + 1, 'field-url',
                    score_of('field-url', near_signature(lines, i)),
                    '.field'
                ))
            for m in HOST_REGEX.finditer(s):
                findings.append(Finding(
                    m.group(1), path, i + 1, 'field-host',
                    score_of('field-host', near_signature(lines, i)),
                    '.field'
                ))
            # 4-2) .field base64-like → 디코딩 후 재탐지
            if BASE64_LIKE.match(s):
                decoded = decode_base64(s)
                if decoded:
                    for m in URL_REGEX.finditer(decoded):
                        findings.append(Finding(
                            m.group(0), path, i + 1, 'field-decoded-url',
                            score_of('field-decoded-url', near_signature(lines, i)),
                            'field-base64'
                        ))
                    for m in HOST_REGEX.finditer(decoded):
                        findings.append(Finding(
                            m.group(1), path, i + 1, 'field-decoded-host',
                            score_of('field-decoded-host', near_signature(lines, i)),
                            'field-base64'
                        ))


    return findings


def dedup(findings):
    best = {}
    for f in findings:
        key = (f.value, f.kind)
        if key not in best or f.score > best[key].score:
            best[key] = f
    return list(best.values())


def normalize(u):
    # http/https는 소문자화 + 경로 기본값 보정
    if u.lower().startswith('http'):
        try:
            from urllib.parse import urlsplit, urlunsplit
            s = urlsplit(u)
            path = s.path or '/'
            return urlunsplit((s.scheme.lower(), s.netloc.lower(), path, s.query, s.fragment))
        except Exception:
            pass
    return u


def format_finding_line(x: dict) -> str:
    """ResultWriter 한 줄 로그 포맷"""
    loc = f"{x['file']}:{x['line']}"
    ctx = f" [{x['context']}]" if x.get('context') else ""
    return f"{x['score']:>3} {x['kind']:<14} {x['value']}  ({loc}){ctx}"


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(
        description='Extract API endpoints/hosts from decompiled Android project (smali/res/..)'
    )
    ap.add_argument('root', help='decompiled project root (smali/ res/ ...)')
    ap.add_argument('-o', '--out', default='endpoints.json', help='JSON 결과 파일 경로')
    ap.add_argument('-l', '--log', default=None, help='라인 로그 파일 경로(미지정 시 콘솔만)')
    ap.add_argument('--top', type=int, default=30, help='요약 출력 개수')
    args = ap.parse_args()

    all_findings = []
    for fp in walk_files(args.root):
        all_findings.extend(extract_from_file(fp))

    all_findings = dedup(all_findings)

    # JSON 결과 구조
    out = []
    for f in all_findings:
        out.append({
            'value': normalize(f.value),
            'kind': f.kind,
            'file': f.file,
            'line': f.line,
            'score': f.score,
            'context': f.context,
        })
    out.sort(key=lambda x: (-x['score'], x['value']))

    # JSON 저장
    with open(args.out, 'w', encoding='utf-8') as w:
        json.dump(out, w, ensure_ascii=False, indent=2)

    # 요약/로그 출력
    writer = ResultWriter(args.log)
    try:
        writer.write(f'found: {len(out)}')
        seen = set()
        for x in out[:args.top]:
            v = x['value']
            if v in seen:
                continue
            writer.write(format_finding_line(x))
            seen.add(v)
    finally:
        writer.close()  

    # 전체 라인 로그가 필요하면 위 writer 블록에서 반복문을 확장하세요.


if __name__ == '__main__':
    main()

'''
사용법 : python extract_endpoint.py <decompiled_project_root> -o endpoints.json -l log.txt --top 30
decompiled_project_root : smali/ res/ 디렉토리가 있는 루트 경로 (apktools로 디컴파일 했을 때 생성되는 디렉토리 경로)
-o : JSON 결과 파일 경로 (기본 endpoints.json)
-l : 라인 로그 파일 경로 (지정하지 않으면 콘솔에만 출력)
--top : 요약 출력 개수 (기본 30)
'''