from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QObject

class SystemTrayIcon(QSystemTrayIcon):
    """系统托盘图标"""
    
    # 定义信号
    showMainWindow = pyqtSignal()  # 显示主窗口
    exitApp = pyqtSignal()         # 退出应用
    nextWallpaper = pyqtSignal()   # 下一张壁纸
    
    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        
        # 设置工具提示
        self.setToolTip("壁纸管理器")
        
        # 创建托盘菜单
        self.menu = QMenu(parent)
        
        # 添加显示主窗口操作
        self.showAction = QAction("显示主窗口", self)
        self.showAction.triggered.connect(self.showMainWindow.emit)
        self.menu.addAction(self.showAction)
        
        # 添加下一张壁纸操作
        self.nextAction = QAction("下一张壁纸", self)
        self.nextAction.triggered.connect(self.nextWallpaper.emit)
        self.menu.addAction(self.nextAction)
        
        self.menu.addSeparator()
        
        # 添加退出操作
        self.exitAction = QAction("退出", self)
        self.exitAction.triggered.connect(self.exitApp.emit)
        self.menu.addAction(self.exitAction)
        
        # 设置托盘菜单
        self.setContextMenu(self.menu)
        
        # 连接激活信号
        self.activated.connect(self.onActivated)
    
    def onActivated(self, reason):
        """处理托盘图标激活事件"""
        # 单击托盘图标时显示主窗口
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showMainWindow.emit()