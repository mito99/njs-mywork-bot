import hashlib
import hmac
from typing import Optional


def verify_slack_signature(
    signing_secret: str, timestamp: str, signature: str, body: str
) -> bool:
    """Slackからのリクエストの署名を検証します。"""
    base = f"v0:{timestamp}:{body}".encode()
    expected = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"v0={expected}", signature)
