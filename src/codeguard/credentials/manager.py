from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet: Fernet | None = None
        self._salt_path = storage_path.with_suffix(".salt")

    def unlock(self, master_password: str) -> bool:
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(key)
        return self._verify()

    def _get_or_create_salt(self) -> bytes:
        if self._salt_path.exists():
            return self._salt_path.read_bytes()
        salt = os.urandom(16)
        self._salt_path.write_bytes(salt)
        self._salt_path.chmod(0o600)
        return salt

    def _verify(self) -> bool:
        if not self._path.exists():
            return True
        try:
            self._read_all()
            return True
        except Exception:
            return False

    def _read_all(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        encrypted = self._path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def _write_all(self, data: dict[str, str]) -> None:
        encrypted = self._fernet.encrypt(json.dumps(data).encode())
        self._path.write_bytes(encrypted)
        self._path.chmod(0o600)

    def store(self, key_name: str, value: str) -> None:
        data = self._read_all()
        data[key_name] = value
        self._write_all(data)

    def get(self, key_name: str) -> str | None:
        data = self._read_all()
        return data.get(key_name)

    def status(self, key_name: str) -> bool:
        data = self._read_all()
        return key_name in data

    def clear(self, key_name: str) -> None:
        data = self._read_all()
        data.pop(key_name, None)
        self._write_all(data)
