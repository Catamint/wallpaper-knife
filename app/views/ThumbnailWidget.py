import base64
from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal, QByteArray, QBuffer, QIODevice, QTimer, QThread, QEvent, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor, QPainter, QPainterPath, QBrush, QPen
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QScrollArea, QLabel

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentIcon as FIF, NavigationItemPosition, CardWidget,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
                          setTheme, Theme, InfoBar, InfoBarPosition, FlowLayout, SearchLineEdit,
                          HyperlinkButton, TitleLabel, PushButton, ToolTipFilter,
                          PrimaryToolButton, TransparentPushButton, FluentStyleSheet,
                          ImageLabel, InfoBadge, SingleDirectionScrollArea)

MINIMUM_HEIGHT = 160  # 固定高度

class RoundedImageLabel(QWidget):
    """圆角图片标签"""
    
    clicked = pyqtSignal()  # 点击信号
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(MINIMUM_HEIGHT)  # 固定高度
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # 宽度自适应，高度固定
        
        # 图片属性
        self._pixmap = QPixmap()
        self._radius = 8  # 圆角半径
        self._text = ""
        self._hovered = False
        
        # 样式属性
        self._bg_color = QColor(50, 50, 50, 30)  # 背景颜色
        self._hover_color = QColor(70, 70, 70, 60)  # 悬停颜色
        self._excluded_color = QColor(80, 80, 80, 100)  # 排除时的背景
        
        # 安装事件过滤器
        self.installEventFilter(self)
        self.setMouseTracking(True)  # 启用鼠标跟踪
    
    def setPixmap(self, pixmap):
        """设置图片"""
        self._pixmap = pixmap
        self.updateGeometry()
        self.update()
    
    def pixmap(self):
        """获取图片"""
        return self._pixmap
    
    def setText(self, text):
        """设置文本"""
        self._text = text
        self.update()
    
    def setExcluded(self, excluded):
        """设置排除状态"""
        self._excluded = excluded
        self.update()
    
    def isExcluded(self):
        """获取排除状态"""
        return self._excluded

    def sizeHint(self):
        """建议大小"""
        if self._pixmap.isNull():
            return QSize(260, MINIMUM_HEIGHT)
            
        # 保持图片比例，固定高度
        height = MINIMUM_HEIGHT
        width = int(self._pixmap.width() * (height / self._pixmap.height()))
        return QSize(width, height)
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        
        # 创建圆角路径
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, int(self._radius), int(self._radius))
        
        # 设置裁剪区域
        painter.setClipPath(path)
        
        # 绘制背景
        if self._excluded:
            painter.fillRect(rect, self._excluded_color)
        elif self._hovered:
            painter.fillRect(rect, self._hover_color)
        else:
            painter.fillRect(rect, self._bg_color)
        
        # 绘制图片
        if not self._pixmap.isNull():
            # 缩放图片以适应控件并保持比例
            scaled_pixmap = self._pixmap.scaled(
                int(rect.width()), int(rect.height()), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 居中绘制 - 修复这里，使用整数坐标
            x = int((rect.width() - scaled_pixmap.width()) / 2)  # 使用整数除法并转换为整数
            y = int((rect.height() - scaled_pixmap.height()) / 2)  # 使用整数除法并转换为整数
            painter.drawPixmap(x, y, scaled_pixmap)  # 使用整数坐标
        elif self._text:
            # 如果没有图片但有文本，绘制文本
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        
        # 绘制边框
        if self._hovered:
            pen = QPen(QColor(200, 200, 255, 100), 2)
            painter.setPen(pen)
            painter.drawPath(path)
    
    def eventFilter(self, obj, event):
        """事件过滤器处理悬停效果"""
        if obj is self:
            if event.type() == QEvent.Type.Enter:
                self._hovered = True
                self.update()
                # 通知父类显示按钮
                if self.parent() and hasattr(self.parent(), 'showButton'):
                    self.parent().showButton()
                    
            elif event.type() == QEvent.Type.Leave:
                self._hovered = False
                self.update()
                # 通知父类隐藏按钮
                if self.parent() and hasattr(self.parent(), 'hideButton'):
                    self.parent().hideButton()
                    
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.clicked.emit()
                
        return super().eventFilter(obj, event)


class ThumbnailWidget(QWidget):
    """简洁版缩略图控件 - 直接使用图片作为卡片"""
    itemClicked = pyqtSignal(str)  # 发送点击信号，包含文件名
    excludeClicked = pyqtSignal(str)  # 排除按钮信号
    includeClicked = pyqtSignal(str)  # 恢复按钮信号
    
    def __init__(self, filename, info, is_excluded=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.info = info
        self.is_excluded = is_excluded
        
        # 设置尺寸策略 - 高度固定，宽度自适应
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(MINIMUM_HEIGHT)  # 最小高度包含图片+文本
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.layout.setSpacing(4)

        # 文件名标签
        display_name = info.display_name
        if len(display_name) > 100:
            display_name = display_name[:97] + "..."        
        # 创建图片标签

        self.image_label = RoundedImageLabel(self)
        self.image_label.setExcluded(is_excluded)
        self.image_label.clicked.connect(self._on_image_clicked)
            
        self.image_label.setToolTip(display_name)
        self.image_label.installEventFilter(ToolTipFilter(self.image_label))
        
        # 创建按钮 (初始隐藏)
        if is_excluded:
            self.action_button = ToolButton(FIF.ACCEPT, self.image_label)
            self.action_button.setToolTip("恢复此壁纸")
            self.action_button.clicked.connect(self._on_include_clicked)
        else:
            self.action_button = ToolButton(FIF.CANCEL, self.image_label)
            self.action_button.setToolTip("排除此壁纸")
            self.action_button.clicked.connect(self._on_exclude_clicked)
            
        self.action_button.setFixedSize(32, 32)
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.installEventFilter(ToolTipFilter(self.action_button))
        self.action_button.hide()  # 初始隐藏
        self.action_button.raise_() # 确保按钮在最上层
        
        # 添加到布局
        self.layout.addWidget(self.image_label)
      
        # 加载缩略图
        self._load_thumbnail()
        
    def showButton(self):
        """显示操作按钮"""
        # 计算按钮位置 - 右上角
        btn_x = self.image_label.width() - self.action_button.width() - 15
        btn_y = 15
        self.action_button.move(btn_x, btn_y)
        self.action_button.show()
        self.action_button.raise_()
    
    def hideButton(self):
        """隐藏操作按钮"""
        self.action_button.hide()
    
    def resizeEvent(self, event):
        """调整大小时重新定位按钮"""
        super().resizeEvent(event)
        if self.action_button.isVisible():
            btn_x = self.image_label.width() - self.action_button.width() - 5
            btn_y = 5
            self.action_button.move(btn_x, btn_y)
    
    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            # 从base64加载
            base64_data = self.info.get_thumbnail_base64()
            pixmap = QPixmap()
            if pixmap.loadFromData(QByteArray.fromBase64(base64_data.encode())):
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("加载失败\n无效的图片数据")
        
        except Exception as e:
            # 加载失败时显示占位图
            self.image_label.setText(f"加载失败\n{str(e)}")
            print(f"加载缩略图时出错: {e}")
    
    def _on_exclude_clicked(self):
        """排除按钮点击事件"""
        self.excludeClicked.emit(self.filename)
        self.is_excluded = True
        self.image_label.setExcluded(True)
        
        # 更换按钮
        self.action_button.deleteLater()
        self.action_button = TransparentToolButton(FIF.ACCEPT, self)
        self.action_button.setToolTip("恢复此壁纸")
        self.action_button.clicked.connect(self._on_include_clicked)
        self.action_button.setFixedSize(32, 32)
        self.showButton()
    
    def _on_include_clicked(self):
        """恢复按钮点击事件"""
        self.includeClicked.emit(self.filename)
        self.is_excluded = False
        self.image_label.setExcluded(False)
        
        # 更换按钮
        self.action_button.deleteLater()
        self.action_button = TransparentToolButton(FIF.CANCEL, self)
        self.action_button.setToolTip("排除此壁纸")
        self.action_button.clicked.connect(self._on_exclude_clicked)
        self.action_button.setFixedSize(32, 32)
        self.showButton()
    
    def _on_image_clicked(self):
        """图片点击事件"""
        self.itemClicked.emit(self.filename)