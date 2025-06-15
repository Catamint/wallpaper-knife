import sys
import os
import argparse
import random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qfluentwidgets import QConfig, setTheme, Theme

from core.config import Config
from core.file_utils import FileUtils
from core.manager import WallpaperManager
from core.image_utils import ImageUtils
from tools.realesrgan import RealesrganTool

from ui.models.settings import wallpaperCfg  # 确保配置类已正确导入

from ui.models.wallpaper_model import WallpaperModel
from ui.controllers.wallpaper_controller import WallpaperController
from ui.views.main_window import WallpaperMainWindow
# import icon

def main():
    # 命令行参数
    parser = argparse.ArgumentParser(description='壁纸刀')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    parser.add_argument('--rebuild', action='store_true', help='重建索引')
    parser.add_argument('--ui', choices=['tk', 'qt'], default='qt', help='选择UI框架 (tk/qt)')
    args = parser.parse_args()
    
    # 初始化核心组件
    config = Config()  # 这将加载settings.json
    file_utils = FileUtils()
    wallpaper_manager = WallpaperManager(config, file_utils)
    
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
        
        if wallpaperCfg.theme == 'dark':
            setTheme(Theme.DARK)
        elif wallpaperCfg.theme == 'light':
            setTheme(Theme.LIGHT)
        else:  # system
            # 根据系统设置判断
            import darkdetect
            if darkdetect.isDark():
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)

        # 创建MVC组件
        model = WallpaperModel(wallpaper_manager)
        image_utils = ImageUtils(config)
        realesrgan_tool = RealesrganTool(config)
        controller = WallpaperController(model, image_utils, realesrgan_tool)
        view = WallpaperMainWindow(controller)
        
        # 连接视图和控制器
        controller.set_view(view)
        
        # 初始化应用
        if args.rebuild:
            controller.rebuild_index()
            
        if controller.initialize():
            # 显示窗口
            view.show()
            sys.exit(app.exec())

if __name__ == "__main__":
    main()