import sys
import os

def _get_base_dir():

    """获取应用程序基础目录"""
    if getattr(sys, 'frozen', False):
        # 如果是打包环境（PyInstaller）
        base_dir = os.path.dirname(sys.executable)
        print(f"运行在打包环境: {base_dir}")
        return base_dir
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"运行在开发环境: {base_dir}")
        return base_dir

# 项目路径
APP_NAME = "WallpaperKnife"
BASE_DIR = _get_base_dir()
WALLPAPER_DIR = os.path.join(BASE_DIR, "wallpapers")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
INDEX_FILE = os.path.join(BASE_DIR, "wallpaper_index.json")
EXCLUDE_FILE = os.path.join(BASE_DIR, "excluded.txt")
APP_ICON = os.path.join(BASE_DIR, "app_icon.png")

# 配置文件路径
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# 日志文件路径
LOG_FILE = os.path.join(BASE_DIR, "app.log")

# 日志级别
LOG_LEVEL = "DEBUG"  # 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 注册表路径（开机启动）
REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# 默认设置
DEFAULT_ROTATION_INTERVAL = 30 * 60  # 30 分钟
