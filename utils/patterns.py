# patterns.py
import re

# URL 전체(스킴 + 바디)
URL_REGEX = re.compile(
    r'(?:(?:h|H)(?:t|T){2}(?:p|P)(?:s|S)?://)[A-Za-z0-9\-\._~:/\?#\[\]@!\$&\'\(\)\*\+,;=%]+'
)

# 스킴 없는 호스트(포트 포함 가능)
HOST_REGEX = re.compile(
    r'\b([A-Za-z0-9\-\.]+\.(?:com|net|org|io|co|me|app|dev|kr|jp|cn|asia|cloud|ai)(?::\d{2,5})?)\b'
)

# smali const-string 상수
CONST_STRING = re.compile(
    r'^\s*const-string(?:/jumbo)?\s+[vp]\d+,\s+"([^"]+)"'
)

# Base64 유사 문자열(난독화 해제 후보)
BASE64_LIKE = re.compile(
    r'^[A-Za-z0-9+/]{20,}={0,2}$'
)

# .field 키워드로 정의된 문자열 상수 패턴 찾기
FIELD_STRING = re.compile(
    r'^\s*\.field\s+(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s+\S+:Ljava/lang/String;\s*=\s*"([^"]+)"'
)

# smali 상에서 Retrofit/OkHttp/URL 관련 시그니처(문맥 가중치에 사용)
_SIGNS_RAW = [
    r'->baseUrl\(Ljava/lang/String;\)Lretrofit2/Retrofit\$Builder;',
    r'->baseUrl\(Lokhttp3/HttpUrl;\)Lretrofit2/Retrofit\$Builder;',
    r'Lokhttp3/Request\$Builder;->url\(Ljava/lang/String;\)Lokhttp3/Request\$Builder;',
    r'Lokhttp3/Request\$Builder;->url\(Lokhttp3/HttpUrl;\)Lokhttp3/Request\$Builder;',
    r'Lokhttp3/HttpUrl;->parse\(Ljava/lang/String;\)Lokhttp3/HttpUrl;',
    r'Lokhttp3/HttpUrl;->get\(Ljava/lang/String;\)Lokhttp3/HttpUrl;',
    r'Ljava/net/URL;-><init>\(Ljava/lang/String;\)V',
]
SIGNS = [re.compile(s) for s in _SIGNS_RAW]

# 기본 검사 확장자
DEFAULT_EXTS = ('.smali', '.xml', '.json', '.properties', '.txt')
