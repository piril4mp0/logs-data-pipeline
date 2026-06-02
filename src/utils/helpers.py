from settings import settings
import urllib.request
import hashlib

def ch_query(sql: str) -> str:
    url = settings.connection_url
    req = urllib.request.Request(url, sql.encode("utf-8"), method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8").strip()

def calc_md5(path: str) -> str:
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()