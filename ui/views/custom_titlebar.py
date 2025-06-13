from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent

class CustomTitleBar(QWidget):
    """自定义标题栏"""
    
    def __init__(self, parent=None, icon_factory=None, title="壁纸管理器"):
        super().__init__(parent)
        self.parent = parent
        self.icon_factory = icon_factory
        self.title = title
        self.setFixedHeight(36)
        self.setup_ui()
        
        # 用于窗口拖动
        self.start = QPoint(0, 0)
        self.pressing = False
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # 应用图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        if self.icon_factory:
            icon = self.icon_factory.get_icon("app_icon")
            pixmap = icon.pixmap(20, 20)
            self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)
        
        # 应用标题
        self.title_label = QLabel(self.title)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label)
        
        # 窗口控制按钮
        self.min_button = QPushButton()
        self.min_button.setObjectName("titleBarButton")
        self.min_button.setFixedSize(30, 30)
        self.min_button.clicked.connect(self.parent.showMinimized)
        
        self.max_button = QPushButton()
        self.max_button.setObjectName("titleBarButton")
        self.max_button.setFixedSize(30, 30)
        self.max_button.clicked.connect(self.toggle_maximize)
        
        self.close_button = QPushButton()
        self.close_button.setObjectName("titleBarCloseButton")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.parent.close)
        
        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)
        
        # 更新按钮图标
        self.update_button_icons(False)  # 默认浅色主题
        
    def update_button_icons(self, dark_mode=False):
        """更新按钮图标"""
        if not self.icon_factory:
            return
            
        self.min_button.setIcon(self.icon_factory.get_icon("minimize", dark_mode))
        self.max_button.setIcon(self.icon_factory.get_icon("maximize" if not self.parent.isMaximized() else "restore", dark_mode))
        self.close_button.setIcon(self.icon_factory.get_icon("close", dark_mode))
    
    def toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
            
        # 更新按钮图标
        dark_mode = getattr(self.parent, "_is_dark_mode", False)
        self.update_button_icons(dark_mode)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressing = True
            self.start = event.pos()
            
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于拖动窗口"""
        if self.pressing and not self.parent.isMaximized():
            self.parent.move(self.parent.pos() + event.pos() - self.start)
            
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self.pressing = False
    
    def mouseDoubleClickEvent(self, event):
        """双击切换最大化/还原"""
        self.toggle_maximize()