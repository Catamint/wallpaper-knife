import os
import hashlib
import json

class FileUtils:
    def __init__(self):
        pass

    def calculate_file_hash(self, filepath):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
