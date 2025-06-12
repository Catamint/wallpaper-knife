import os
import sys
import tkinter as tk
import argparse

from core.config import Config
from core.file_utils import FileUtils
from core.manager import WallpaperManager
from core.image_utils import ImageUtils
from tools.realesrgan import RealesrganTool
from ui.tk_app import WallpaperTkApp

def main():
    # 命令行参数
    parser = argparse.ArgumentParser(description='壁纸管理器')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--rebuild', action='store_true', help='重建索引')
    args = parser.parse_args()
    
    # 初始化核心组件
    config = Config()
    file_utils = FileUtils(config)
    image_utils = ImageUtils(config)
    realesrgan_tool = RealesrganTool(config)
    wallpaper_manager = WallpaperManager(config, file_utils)
    
    if args.cli:
        # 命令行模式
        print("命令行模式")
        if not wallpaper_manager.load_index() or args.rebuild:
            print("构建索引中...")
            wallpaper_manager.build_index(lambda c, t, f: print(f"处理中: {c+1}/{t} - {f}"))
        
        # 这里可以实现命令行交互
        while True:
            command = input("输入命令 (next/prev/crop/exclude/exit): ").strip().lower()
            if command == 'get':
                wallpaper_manager.get_wallpaper_list()
            elif command == 'set':
                temp_path = input("输入壁纸路径: ").strip()
                if os.path.exists(temp_path):
                    wallpaper_manager.set_wallpaper(temp_path, async_mode=False)
            elif command == 'crop':
                # 处理裁剪逻辑
                pass
            elif command == 'exclude':
                # 处理排除逻辑
                pass
            elif command == 'exit':
                break
            else:
                print("未知命令，请重试。")
    else:
        # GUI模式
        root = tk.Tk()
        root.geometry("800x600")
        app = WallpaperTkApp(root, wallpaper_manager, file_utils, image_utils, realesrgan_tool)
        root.mainloop()

if __name__ == "__main__":
    main()