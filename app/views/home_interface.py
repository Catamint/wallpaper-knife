from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
import os  # 确保导入os模块

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentWindow, FluentIcon as FIF, NavigationItemPosition,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, 
                          setTheme, Theme, InfoBar, InfoBarPosition, PrimaryToolButton, ToolTipFilter)

from .crop_view import CropGraphicsView

class HomeInterface(QFrame):
    """主页界面"""
    
    # 定义信号
    cropRequested = pyqtSignal(object)  # 发送裁剪区域对象
    
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.setObjectName("Home-Interface")
        self.setup_ui()
    
    def setup_ui(self):
        """设置主页界面"""
        layout = QVBoxLayout(self)
        
        # 图像显示区域
        self.image_view = CropGraphicsView()
        self.image_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.image_view, 1)
        
        # 底部控制栏
        bottom_layout = QHBoxLayout()
        
        # 随机壁纸按钮
        self.random_button = PrimaryToolButton(FIF.CAFE)
        self.random_button.setToolTip("随机壁纸")
        self.random_button.setIconSize(QSize(20, 20))
        self.random_button.installEventFilter(ToolTipFilter(self.random_button))
        self.random_button.clicked.connect(self.safe_random_wallpaper)
        bottom_layout.addWidget(self.random_button)

        # 导航按钮组
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        # 上一张按钮
        self.prev_button = ToolButton(FIF.LEFT_ARROW)
        self.prev_button.setIconSize(QSize(20, 20))
        self.prev_button.setToolTip("上一张壁纸")
        self.prev_button.installEventFilter(ToolTipFilter(self.prev_button))
        self.prev_button.clicked.connect(self.safe_prev_wallpaper)
        nav_layout.addWidget(self.prev_button)
        
        # 下一张按钮
        self.next_button = ToolButton(FIF.RIGHT_ARROW)
        self.next_button.setIconSize(QSize(20, 20))
        self.next_button.setToolTip("下一张壁纸")
        self.next_button.installEventFilter(ToolTipFilter(self.next_button))
        self.next_button.clicked.connect(self.safe_next_wallpaper)
        nav_layout.addWidget(self.next_button)

        # 排除当前按钮
        self.exclude_button = TransparentToolButton(FIF.CANCEL)
        self.exclude_button.setToolTip("排除当前壁纸")
        self.exclude_button.setIconSize(QSize(20, 20))
        self.exclude_button.installEventFilter(ToolTipFilter(self.exclude_button))
        self.exclude_button.clicked.connect(self.safe_exclude_wallpaper)
        nav_layout.addWidget(self.exclude_button)

        bottom_layout.addLayout(nav_layout)
        bottom_layout.addStretch(1)

        # 当前壁纸信息
        self.info_label = CaptionLabel("正在加载壁纸...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bottom_layout.addWidget(self.info_label)
        
        # 应用裁剪按钮
        self.crop_button = PrimaryPushButton("应用裁剪")
        self.crop_button.setIcon(FIF.CUT)
        self.crop_button.setToolTip("应用裁剪")
        self.crop_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.crop_button.setIconSize(QSize(20, 20))
        self.crop_button.installEventFilter(ToolTipFilter(self.crop_button))
        self.crop_button.clicked.connect(self.on_apply_crop)
        bottom_layout.addWidget(self.crop_button)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(bottom_layout)
    
    def safe_random_wallpaper(self):
        """安全的随机壁纸方法"""
        try:
            if hasattr(self.controller, 'random_wallpaper'):
                self.controller.random_wallpaper()
            else:
                self.show_error("随机壁纸功能未实现")
        except Exception as e:
            self.show_error(f"随机壁纸时出错: {str(e)}")

    def safe_set_wallpaper(self):
        """安全的设置壁纸方法"""
        try:
            if hasattr(self.controller, 'set_current_wallpaper'):
                self.controller.set_current_wallpaper()
            else:
                self.show_error("设置壁纸功能未实现")
        except Exception as e:
            self.show_error(f"设置壁纸时出错: {str(e)}")
    
    def safe_prev_wallpaper(self):
        """安全的上一张壁纸方法"""
        try:
            if hasattr(self.controller, 'prev_wallpaper'):
                self.controller.prev_wallpaper()
            else:
                self.show_error("上一张功能未实现")
        except Exception as e:
            self.show_error(f"切换上一张壁纸时出错: {str(e)}")
    
    def safe_next_wallpaper(self):
        """安全的下一张壁纸方法"""
        try:
            if hasattr(self.controller, 'next_wallpaper'):
                self.controller.next_wallpaper()
            else:
                self.show_error("下一张功能未实现")
        except Exception as e:
            self.show_error(f"切换下一张壁纸时出错: {str(e)}")
    
    def safe_exclude_wallpaper(self):
        """安全的排除壁纸方法"""
        try:
            if hasattr(self.controller, 'exclude_wallpaper'):
                self.controller.exclude_wallpaper()
            else:
                self.show_error("排除功能未实现")
        except Exception as e:
            self.show_error(f"排除壁纸时出错: {str(e)}")

    def get_crop_rect(self):
        """获取当前的裁剪区域"""
        try:
            if hasattr(self, 'image_view') and hasattr(self.image_view, 'getCropRect'):
                return self.image_view.getCropRect()
            return None
        except Exception as e:
            print(f"获取裁剪区域时出错: {e}")
            return None

    def on_apply_crop(self):
        """应用裁剪 - 使用信号机制"""
        try:
            crop_rect = self.get_crop_rect()
            if crop_rect:
                # 发送信号而不是直接调用控制器
                self.cropRequested.emit(crop_rect)
            else:
                InfoBar.warning(
                    title='警告',
                    content='请先选择裁剪区域',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            self.show_error(f"应用裁剪时出错: {str(e)}")
    
    def show_error(self, message):
        """显示错误信息"""
        InfoBar.error(
            title='错误',
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
    
    def update_wallpaper(self, picture):
        """更新显示的壁纸
        
        Args:
            picture (Picture): 壁纸对象
        """
        try:
            if picture is None:
                raise Exception("无效的壁纸对象")
                
            # 加载图片
            pixmap = QPixmap(picture.path)
            if pixmap.isNull():
                raise Exception(f"无法加载图片: {picture.path}")
                
            # 显示图片
            self.image_view.setImage(pixmap)
            
            # 更新状态
            display_name = picture.display_name
            
            # 从控制器获取当前索引位置和总数
            filtered_pictures = self.controller.index_manager.get_filtered_pictures(excluded=False)
            
            try:
                current_index = filtered_pictures.index(picture) + 1  # 从1开始计数
            except ValueError:
                # 如果当前图片不在过滤列表中，可能是排除状态
                current_index = 0
                
            total = len(filtered_pictures)
            
            # 更新信息标签
            if current_index > 0:
                self.info_label.setText(f"{display_name} ({current_index}/{total})")
            else:
                self.info_label.setText(f"{display_name} (已排除)")
            
        except Exception as e:
            self.show_error(f'加载图片失败: {str(e)}')
            # 尝试排除问题壁纸
            if hasattr(self.controller, 'exclude_current') and picture == self.controller.current_picture:
                self.controller.exclude_current()