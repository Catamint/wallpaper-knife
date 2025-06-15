import sys
import os
import argparse
import random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qfluentwidgets import setTheme

from app.models.manager import WallpaperManager
from app.models.wallpaper_model import WallpaperModel
from app.controllers.wallpaper_controller import WallpaperController
from app.views.main_window import WallpaperMainWindow

from app.models.settings import wallpaperCfg  # 确保配置类已正确导入

def main():
    # 命令行参数
    parser = argparse.ArgumentParser(description='壁纸刀')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--rebuild', action='store_true', help='重建索引')
    args = parser.parse_args()
    
    # 初始化核心组件
    wallpaper_manager = WallpaperManager()
    
    # 设置随机种子
    random.seed()
    
    if args.cli:
        # 命令行模式
        print("命令行模式")
        if not wallpaper_manager.load_index() or args.rebuild:
            print("构建索引中...")
            wallpaper_manager.build_index(lambda c, t, f: print(f"处理中: {c}/{t} - {f}"))
        
        # 这里可以实现命令行交互
        while True:
            command = input("输入命令 (next/prev/crop/exclude/exit): ").strip().lower()
            # ...命令处理逻辑...
            if command == 'exit':
                break
    else:
        # GUI模式
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'app_icon.png')))

        # 创建MVC组件
        model = WallpaperModel(wallpaper_manager)
        controller = WallpaperController(model)
        view = WallpaperMainWindow(controller)
        
        # 连接视图和控制器
        controller.set_view(view)
        
        # 初始化应用
        if args.rebuild:
            controller.rebuild_index()
            
        if controller.initialize():
            # 显示窗口
            setTheme(wallpaperCfg.defaultTheme.value)
            view.show()
            sys.exit(app.exec())

if __name__ == "__main__":
    main()