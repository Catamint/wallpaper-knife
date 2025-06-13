from PyQt6.QtWidgets import (QMainWindow, QWidget, QPushButton, 
                           QVBoxLayout, QHBoxLayout, QLabel, QSplitter)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction  # 保留这个导入，可能在其他地方使用到

from .crop_view import CropGraphicsView
from ..styles.light_theme import LIGHT_THEME
from ..styles.dark_theme import DARK_THEME

# 首先，导入图库视图
from .gallery_view import GalleryView

class WallpaperMainWindow(QMainWindow):
    """壁纸管理主窗口"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("壁纸管理器")
        self.setMinimumSize(480, 320)
        
        self.setup_ui()
        self.load_theme()
        
    def setup_ui(self):
        """设置UI"""
        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 图像显示区域
        self.image_view = CropGraphicsView()
        self.main_layout.addWidget(self.image_view, 1)
        
        # 按钮区域
        self.button_layout = QHBoxLayout()
        
        # 使用 Windows 11 风格的按钮
        self.prev_button = QPushButton("上一张")
        self.prev_button.clicked.connect(self.controller.prev_wallpaper)
        self.prev_button.setProperty("class", "accent-button")
        self.button_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一张")
        self.next_button.clicked.connect(self.controller.next_wallpaper)
        self.next_button.setProperty("class", "accent-button")
        self.button_layout.addWidget(self.next_button)
        
        self.crop_button = QPushButton("应用裁剪")
        self.crop_button.clicked.connect(self.on_apply_crop)
        self.button_layout.addWidget(self.crop_button)
        
        self.exclude_button = QPushButton("排除当前")
        self.exclude_button.clicked.connect(self.controller.exclude_wallpaper)
        self.button_layout.addWidget(self.exclude_button)
        
        self.refresh_button = QPushButton("刷新索引")
        self.refresh_button.clicked.connect(self.controller.refresh_index)
        self.button_layout.addWidget(self.refresh_button)
        
        self.theme_button = QPushButton("深色模式")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.button_layout.addWidget(self.theme_button)
        
        # 图库按钮
        self.gallery_button = QPushButton("图库")
        self.gallery_button.clicked.connect(self.show_gallery_dialog)
        self.button_layout.addWidget(self.gallery_button)
        
        # 新增设置按钮
        self.settings_button = QPushButton("设置")
        self.settings_button.clicked.connect(self.show_settings)
        self.button_layout.addWidget(self.settings_button)
        
        self.main_layout.addLayout(self.button_layout)
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_label = QLabel("准备中...")
        self.status_bar.addWidget(self.status_label, 1)
        
        # 移除菜单栏相关代码
    
    def load_theme(self, dark_mode=False):
        """加载主题"""
        if dark_mode:
            self.setStyleSheet(DARK_THEME)
            self.theme_button.setText("浅色模式")
            self._is_dark_mode = True
        else:
            self.setStyleSheet(LIGHT_THEME)
            self.theme_button.setText("深色模式")
            self._is_dark_mode = False
    
    def toggle_theme(self):
        """切换主题"""
        self.load_theme(not self._is_dark_mode)
    
    @pyqtSlot()
    def on_apply_crop(self):
        """应用裁剪"""
        crop_rect = self.image_view.getCropRect()
        if crop_rect:
            self.controller.apply_crop(crop_rect)
        else:
            from .dialogs import show_warning
            show_warning(self, "警告", "请先选择裁剪区域")
    
    @pyqtSlot(str, dict)
    def update_wallpaper(self, filename, info):
        """更新显示的壁纸"""
        try:
            from PyQt6.QtGui import QPixmap
            import os
            
            # 加载图片
            pixmap = QPixmap(info["path"])
            if pixmap.isNull():
                raise Exception("无法加载图片")
                
            # 显示图片 (这会自动清除旧的裁剪矩形)
            self.image_view.setImage(pixmap)
            
            # 更新状态
            display_name = info.get("display_name", os.path.basename(info["path"]))
            wallpaper_list = self.controller.model.wallpaper_list
            current_index = self.controller.model.current_index
            total = len(wallpaper_list)
            self.status_label.setText(f"{display_name} ({current_index+1}/{total})")
            self.setWindowTitle(f"壁纸管理器 - {display_name}")
            
        except Exception as e:
            from .dialogs import show_error
            show_error(self, "错误", f"加载图片失败: {str(e)}")
            self.controller.exclude_wallpaper()
    
    def show_gallery_dialog(self):
        """显示图库对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        self.gallery_dialog = QDialog(self)
        self.gallery_dialog.setWindowTitle("壁纸图库")
        self.gallery_dialog.setMinimumSize(800, 600)
        dialog_layout = QVBoxLayout(self.gallery_dialog)
        
        # 创建图库视图
        self.gallery_view = GalleryView()
        dialog_layout.addWidget(self.gallery_view)
        
        # 连接信号
        self.gallery_view.wallpaperSelected.connect(self.controller.select_wallpaper_from_gallery)
        self.gallery_view.excludeWallpaper.connect(self.controller.exclude_wallpaper)
        self.gallery_view.includeWallpaper.connect(self.controller.include_wallpaper)
        
        # 显示图库
        self.gallery_dialog.show()
        
        # 请求加载壁纸数据
        self.controller.open_gallery()

    def show_gallery(self, wallpaper_data):
        """显示图库数据"""
        if hasattr(self, 'gallery_view') and self.gallery_view:
            self.gallery_view.set_data(wallpaper_data)

    def close_gallery(self):
        """关闭图库对话框"""
        if hasattr(self, 'gallery_dialog') and self.gallery_dialog:
            self.gallery_dialog.accept()
    
    def show_settings(self):
        """显示设置对话框"""
        from ..views.settings_dialog import SettingsDialog
        
        settings_dialog = SettingsDialog(self.controller.model.manager.config, self)
        settings_dialog.settingsChanged.connect(self.on_settings_changed)
        settings_dialog.exec()

    def on_settings_changed(self):
        """当设置更改时响应"""
        # 重新加载主题
        config = self.controller.model.manager.config
        if hasattr(self, '_is_dark_mode'):
            self.load_theme(config.THEME == "dark")
        
        # 更新动画设置
        self.enable_animations(config.ENABLE_ANIMATIONS)
        
        # 其他可能需要响应设置变化的地方
        self.controller.settings_changed()