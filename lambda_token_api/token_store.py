# token_store.py
import threading
import time
import json
from typing import Optional, List
from omnipilot.config import CLIENT_KEY, CLIENT_SECRET, TOKEN_URL
import requests
import logging
import boto3
from botocore.exceptions import ClientError

TOKEN_FILE = "tiktok_tokens.json"
BUCKET_NAME = "tiktok-token-store"
OBJECT_KEY = "tiktok_tokens.json"

s3 = boto3.client("s3", region_name="ap-northeast-1")
_lock = threading.Lock()


class TokenStore:

    @classmethod
    def _load_raw_tokens(cls) -> Optional[dict]:
        try:
            response = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return {}
            raise
        except Exception:
            return {}

    @classmethod
    def _save_raw_tokens(cls, tokens: dict):
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=OBJECT_KEY,
            Body=json.dumps(tokens, indent=2),
            ContentType="application/json",
        )

    @classmethod
    def save_token(cls, token: dict, open_id: Optional[str] = None):
        """トークンをファイルに保存する"""
        if not token:
            return token

        with _lock:
            if "expires_in" in token and "expires_at" not in token:
                token["expires_at"] = time.time() + token["expires_in"]

            target_open_id = open_id or token.get("open_id")

            tokens = cls._load_raw_tokens() or {}
            tokens[target_open_id] = token
            cls._save_raw_tokens(tokens)

        return token

    @classmethod
    def load_token(cls, open_id: str) -> Optional[dict]:
        """指定されたopen_idのトークンを読み込む"""
        target_open_id = open_id

        with _lock:
            tokens = cls._load_raw_tokens()
            if not tokens:
                return None
            return tokens.get(target_open_id)

    @classmethod
    def get_access_token(cls, open_id: str) -> Optional[str]:
        """参照＋期限切れ判定＋自動更新"""
        target_open_id = open_id
        token = cls.load_token(target_open_id)
        if not token:
            return None

        now = time.time()
        if token.get("expires_at", 0) <= now:
            refresh_token = token.get("refresh_token")
            if refresh_token:
                new = cls._refresh(refresh_token, target_open_id)
                return new.get("access_token") if new else None
            return None
        return token.get("access_token")

    @classmethod
    def _refresh(cls, refresh_token: str, open_id: str) -> Optional[dict]:
        """トークンを更新"""
        if not refresh_token:
            return None

        data = {
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        resp = requests.post(TOKEN_URL, data=data)
        if resp.status_code != 200:
            logging.error(f"[TokenStore] refresh failed for {open_id}: {resp.text}")
            return None
        token = resp.json()
        cls.save_token(token, open_id)
        return token

    @classmethod
    def list_accounts(cls) -> List[str]:
        """保存されているアカウントのopen_idリストを取得"""
        with _lock:
            tokens = cls._load_raw_tokens()
            return list(tokens.keys()) if tokens else []

    @classmethod
    def delete_account(cls, open_id: str) -> bool:
        """指定されたアカウントのトークンを削除"""
        with _lock:
            tokens = cls._load_raw_tokens()
            if not tokens or open_id not in tokens:
                return False

            del tokens[open_id]
            cls._save_raw_tokens(tokens)
            return True

    @classmethod
    def has_account(cls, open_id: str) -> bool:
        """指定されたアカウントのトークンが存在するかチェック"""
        return cls.load_token(open_id) is not None
