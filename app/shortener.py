import re
import secrets
import string
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits

def generate_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url.strip())
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False

def validate_custom_code(code: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,30}$", code))
