from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QApplication, QSystemTrayIcon
import os  # 添加导入os模块

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentWindow, FluentIcon as FIF, NavigationItemPosition,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, 
                          setTheme, Theme, InfoBar, InfoBarPosition)

from .crop_view import CropGraphicsView
from .home_interface import HomeInterface
from .gallery_interface import GalleryInterface
from .settings_interface import SettingsInterface

# 导入托盘类
from .tray_icon import SystemTrayIcon

from .. import wallpaperCfg

class WallpaperMainWindow(FluentWindow):
    """使用QFluentWidgets的壁纸管理主窗口"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        # 创建子界面
        self.homeInterface = HomeInterface(controller, self)
        self.galleryInterface = GalleryInterface(controller, self)
        self.settingsInterface = SettingsInterface(controller, self)
        
        # 连接信号
        self.connect_signals()
        
        self.initNavigation()
        self.initWindow()
        
        # 设置托盘图标
        self.setup_tray_icon()
    
    def connect_signals(self):
        """连接各界面的信号"""
        # 连接裁剪请求信号
        if hasattr(self.homeInterface, 'cropRequested'):
            self.homeInterface.cropRequested.connect(self.handle_crop_request)
        
    def handle_crop_request(self, crop_rect):
        """处理裁剪请求"""
        try:
            if hasattr(self.controller, 'apply_crop'):
                self.controller.apply_crop(crop_rect)
            else:
                InfoBar.warning(
                    title='功能未实现',
                    content='裁剪功能未实现',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'应用裁剪时出错: {str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
    
    def initNavigation(self):
        """初始化导航"""
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')
        self.addSubInterface(self.galleryInterface, FIF.PHOTO, '图库')
        self.addSubInterface(self.settingsInterface, FIF.SETTING, '设置')
        
        # 添加额外的功能项
        self.navigationInterface.addItem(
            routeKey='refresh',
            icon=FIF.SYNC,
            text='重新索引',
            onClick=self.safe_refresh_index,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 添加主题切换
        self.navigationInterface.addItem(
            routeKey='theme',
            icon=FIF.BRUSH,
            text='切换主题',
            onClick=self.toggle_theme,
            position=NavigationItemPosition.BOTTOM
        )
    
    def initWindow(self):
        """初始化窗口"""
        self.setWindowTitle("壁纸刀")
        self.resize(900, 600)
        
        # 根据系统主题设置初始主题
        self.load_theme()
        
        # 设置窗口图标
        # self.setWindowIcon(FIF.PHOTO.icon())
    
    def safe_refresh_index(self):
        """安全的刷新索引方法"""
        try:
            if hasattr(self.controller, 'refresh_index'):
                self.controller.refresh_index()
            elif hasattr(self.controller, 'rebuild_index'):
                self.controller.rebuild_index()
            else:
                InfoBar.warning(
                    title='功能未实现',
                    content='刷新索引功能未实现',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'刷新索引时出错: {str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
    
    def load_theme(self, dark_mode=False):
        """加载主题"""
        if dark_mode:
            setTheme(Theme.DARK)
            self._is_dark_mode = True
        else:
            setTheme(Theme.LIGHT)
            self._is_dark_mode = False
    
    def toggle_theme(self):
        """切换主题"""
        if hasattr(self, '_is_dark_mode'):
            next_mode = not self._is_dark_mode
        else:
            next_mode = True
        self.load_theme(next_mode)
    
    def update_wallpaper(self, key, info):
        """更新显示的壁纸
        
        Args:
            key: 壁纸的唯一标识符
            info: 壁纸的详细信息字典
        """
        # 委托给主页界面处理
        self.homeInterface.update_wallpaper(key, info)
        
        # 更新窗口标题
        display_name = info.get("display_name") or os.path.basename(info.get("path", ""))
        self.setWindowTitle(f"壁纸刀 - {display_name}")
    
    def show_gallery(self, wallpaper_data):
        """显示图库数据"""
        self.galleryInterface.set_data(wallpaper_data)
        self.stackedWidget.setCurrentWidget(self.galleryInterface)
    
    def close_gallery(self):
        """关闭图库，返回主界面"""
        self.stackedWidget.setCurrentWidget(self.homeInterface)
    
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        app_icon = QIcon("app_icon.png")  # 替换为你的应用图标路径
        self.tray_icon = SystemTrayIcon(app_icon, self)
        
        # 连接信号
        self.tray_icon.showMainWindow.connect(self.show_from_tray)
        self.tray_icon.exitApp.connect(self.exit_application)
        self.tray_icon.nextWallpaper.connect(self.next_wallpaper)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def show_from_tray(self):
        """从托盘图标显示窗口"""
        self.showNormal()
        self.activateWindow()
    
    def exit_application(self):
        """退出应用程序"""
        if hasattr(self.controller, 'cleanup'):
            self.controller.cleanup()
        QApplication.quit()
    
    def next_wallpaper(self):
        """切换到下一张壁纸"""
        if hasattr(self.controller, 'next_wallpaper'):
            self.controller.next_wallpaper()
    
    def statusBar(self):
        """提供兼容层以支持传统的statusBar().showMessage()调用"""
        class StatusBarCompat:
            def __init__(self, window):
                self.window = window
                
            def showMessage(self, message, timeout=0):
                """显示状态栏消息"""
                if hasattr(self.window.homeInterface, 'info_label'):
                    self.window.homeInterface.info_label.setText(message)
                    
        return StatusBarCompat(self)
    
    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # 如果托盘图标存在并可见，最小化到托盘
            self.hide()
            
            # 显示通知
            if wallpaperCfg.notifications.value:
                self.tray_icon.showMessage(
                    "壁纸刀",
                    "应用程序已最小化到系统托盘，点击图标恢复。",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            
            # 阻止应用关闭
            event.ignore()
        else:
            # 否则执行默认的关闭操作
            super().closeEvent(event)