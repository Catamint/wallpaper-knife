import os
import hashlib
import json

class FileUtils:
    def __init__(self, config):
        self.config = config

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
            
    def get_excluded(self):
        if not os.path.exists(self.config.EXCLUDE_FILE):
            return set()
        try:
            with open(self.config.EXCLUDE_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"读取排除文件失败: {e}")
            return set()
            
    def add_to_excluded(self, filename):
        try:
            with open(self.config.EXCLUDE_FILE, 'a', encoding='utf-8') as f:
                f.write(filename + '\n')
        except Exception as e:
            print(f"写入排除文件失败: {e}")