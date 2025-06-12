from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
                            QSplitter, QGraphicsView, QGraphicsScene)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QRectF, QPoint
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush
import sys
import os
import random

class CropGraphicsView(QGraphicsView):
    """裁剪图片视图"""
    cropSelected = pyqtSignal(QRectF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 裁剪区域
        self.start_point = None
        self.current_rect = None
        self.crop_rect_item = None
        
        # 设置为可交互
        self.setMouseTracking(True)
        self.setInteractive(True)
        
    def setImage(self, pixmap):
        """设置图片"""
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        
        # 使用浮点数创建 QRectF
        rect = pixmap.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        self.scene.setSceneRect(QRectF(float(x), float(y), float(w), float(h)))
        
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def mousePressEvent(self, event):
        """鼠标按下，开始裁剪"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = self.mapToScene(event.pos())
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = None
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动，更新裁剪框"""
        if self.start_point and event.buttons() & Qt.MouseButton.LeftButton:
            end_point = self.mapToScene(event.pos())
            
            # 更新矩形
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
            
            rect = QRectF(self.start_point, end_point).normalized()
            self.current_rect = rect
            
            # 绘制新矩形
            self.crop_rect_item = self.scene.addRect(
                rect, 
                QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine),
                QBrush(QColor(255, 0, 0, 30))
            )
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放，完成裁剪选择"""
        if event.button() == Qt.MouseButton.LeftButton and self.start_point and self.current_rect:
            self.cropSelected.emit(self.current_rect)
            self.start_point = None
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        """窗口大小变化时，调整图像大小"""
        if self.scene and not self.scene.items():
            return
            
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)

class IndexBuilderThread(QThread):
    """索引构建线程"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool)
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    def run(self):
        """运行索引构建"""
        success = self.manager.build_index(self._progress_callback)
        self.finished.emit(success)
    
    def _progress_callback(self, current, total, filename):
        """进度回调"""
        self.progress.emit(current, total, filename)

class WallpaperQtApp(QMainWindow):
    def __init__(self, wallpaper_manager, file_utils, image_utils, realesrgan_tool):
        super().__init__()
        self.manager = wallpaper_manager
        self.file_utils = file_utils
        self.image_utils = image_utils
        self.realesrgan = realesrgan_tool
        
        self.current_index = 0
        self.wallpaper_list = []
        self.excluded_files = set()
        self.random_seed = random.randint(1, 1000000)
        
        self.setWindowTitle("壁纸管理器")
        self.setMinimumSize(1024, 768)
        
        self.setup_ui()
        self.initialize_data()
        
    def setup_ui(self):
        """设置UI"""
        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 图像显示区域
        self.image_view = CropGraphicsView()
        self.image_view.cropSelected.connect(self.on_crop_selected)
        self.main_layout.addWidget(self.image_view, 1)
        
        # 按钮区域
        self.button_layout = QHBoxLayout()
        
        # 使用 Windows 11 风格的按钮
        self.prev_button = QPushButton("上一张")
        self.prev_button.clicked.connect(self.prev_wallpaper)
        self.prev_button.setProperty("class", "accent-button")
        self.button_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一张")
        self.next_button.clicked.connect(self.next_wallpaper)
        self.next_button.setProperty("class", "accent-button")
        self.button_layout.addWidget(self.next_button)
        
        self.crop_button = QPushButton("应用裁剪")
        self.crop_button.clicked.connect(self.apply_crop)
        self.button_layout.addWidget(self.crop_button)
        
        self.exclude_button = QPushButton("排除当前")
        self.exclude_button.clicked.connect(self.exclude_wallpaper)
        self.button_layout.addWidget(self.exclude_button)
        
        self.refresh_button = QPushButton("刷新索引")
        self.refresh_button.clicked.connect(self.refresh_index)
        self.button_layout.addWidget(self.refresh_button)
        
        self.main_layout.addLayout(self.button_layout)
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_label = QLabel("准备中...")
        self.status_bar.addWidget(self.status_label, 1)
        
        # 应用样式表
        self.apply_win11_style()

        
    def apply_win11_style(self):
        """应用 Windows 11 风格样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
            }
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px 16px;
                min-width: 80px;
                color: #202020;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton[class="accent-button"] {
                background-color: #0078d4;
                color: white;
                border: none;
            }
            QPushButton[class="accent-button"]:hover {
                background-color: #106ebe;
            }
            QPushButton[class="accent-button"]:pressed {
                background-color: #005a9e;
            }
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #505050;
            }
        """)
    def toggle_dark_mode(self, enabled=True):
        """切换深色/浅色模式"""
        if enabled:
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #202020;
                    color: #e0e0e0;
                }
                QPushButton {
                    background-color: #323232;
                    border: 1px solid #505050;
                    color: #e0e0e0;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
                QPushButton[class="accent-button"] {
                    background-color: #0078d4;
                    color: white;
                }
                /* ...其他样式... */
            """)
        else:
            self.apply_win11_style()  # 回到亮色模式
        
    def show_progress_dialog(self, title, message):
        """显示进度对话框"""
        from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QProgressBar
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        message_label = QLabel(message)
        layout.addWidget(message_label)
        
        progress_label = QLabel("准备中...")
        layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)
        
        # 创建并启动构建线程
        self.builder_thread = IndexBuilderThread(self.manager)
        self.builder_thread.progress.connect(
            lambda current, total, filename: self.update_progress(
                progress_bar, progress_label, current, total, filename)
        )
        self.builder_thread.finished.connect(lambda success: dialog.accept() if success else dialog.reject())
        self.builder_thread.start()
        
        # 显示对话框
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    def update_progress(self, progress_bar, label, current, total, filename):
        """更新进度"""
        progress_bar.setValue(int(100 * current / max(1, total)))
        label.setText(f"处理中: {current+1}/{total} - {os.path.basename(filename)}")
    
    def initialize_data(self):
        """初始化数据"""
        self.excluded_files = self.file_utils.get_excluded()
        
        # 检查是否需要重建索引
        if not self.manager.load_index() or self.need_rebuild_index():
            if not self.rebuild_index():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", "构建索引失败!")
                return
        
        self.wallpaper_list = [f for f in self.manager.get_wallpaper_list() 
                             if f not in self.excluded_files]
        
        if self.wallpaper_list:
            random.seed(self.random_seed)
            random.shuffle(self.wallpaper_list)
            # 异步加载第一张图片
            QApplication.processEvents()
            self.load_wallpaper()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", "没有可用的壁纸!")
    
    def rebuild_index(self):
        """重建索引"""
        return self.show_progress_dialog("构建索引", "正在构建壁纸索引...")
    
    def need_rebuild_index(self):
        """检查是否需要重建索引"""
        if not os.path.exists(self.manager.config.WALLPAPER_DIR):
            return False
        
        current_mtime = os.path.getmtime(self.manager.config.WALLPAPER_DIR)
        last_mtime = self.manager.index_data.get("last_updated", 0)
        
        return current_mtime > last_mtime
    
    def load_wallpaper(self):
        """加载当前壁纸"""
        if not self.wallpaper_list:
            return
            
        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]
        
        try:
            # 加载图片
            pixmap = QPixmap(wallpaper_info["path"])
            if pixmap.isNull():
                raise Exception("无法加载图片")
                
            # 显示图片
            self.image_view.setImage(pixmap)
            
            # 自动设置为壁纸（使用缓存或原图）
            self.set_current_wallpaper()
            
            # 更新状态
            display_name = wallpaper_info.get("display_name", os.path.basename(wallpaper_info["path"]))
            total = len(self.wallpaper_list)
            self.status_label.setText(f"{display_name} ({self.current_index+1}/{total})")
            self.setWindowTitle(f"壁纸管理器 - {display_name}")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"加载图片失败: {str(e)}")
            self.exclude_wallpaper()
    
    def set_current_wallpaper(self):
        """设置当前壁纸（优先使用缓存）"""
        # 与原有方法相同，但使用Qt的错误处理
        if not self.wallpaper_list:
            return

        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]

        # 优先使用缓存文件
        if wallpaper_info.get("cache_path") and wallpaper_info["cache_path"]:
            cache_path = os.path.join(self.manager.config.CACHE_DIR, wallpaper_info["cache_path"])
            if os.path.exists(cache_path):
                self.manager.set_wallpaper(cache_path)
                return
        
        # 使用原图
        self.manager.set_wallpaper(wallpaper_info["path"])
    
    def prev_wallpaper(self):
        """上一张壁纸"""
        if self.wallpaper_list:
            self.current_index = (self.current_index - 1) % len(self.wallpaper_list)
            self.load_wallpaper()
    
    def next_wallpaper(self):
        """下一张壁纸"""
        if self.wallpaper_list:
            self.current_index = (self.current_index + 1) % len(self.wallpaper_list)
            self.load_wallpaper()
            
    def on_crop_selected(self, rect):
        """裁剪区域选择完成"""
        # 仅存储选择的矩形，不立即应用
        self.selected_crop_rect = rect
    
    def apply_crop(self):
        """应用裁剪"""
        # 检查是否有选择的裁剪区域
        if not hasattr(self, 'selected_crop_rect') or not self.selected_crop_rect or not self.wallpaper_list:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请先选择裁剪区域")
            return
        
        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]
        
        try:
            # 实现裁剪逻辑...（与tk_app.py类似，但使用Qt的图像处理）
            from PyQt6.QtGui import QImage
            from PyQt6.QtCore import QRectF
            from screeninfo import get_monitors
            
            # 加载原图
            original_img = QImage(wallpaper_info["path"])
            
            # 获取裁剪矩形
            scene_rect = self.image_view.scene.sceneRect()
            view_rect = self.image_view.viewport().rect()
            
            # 计算缩放比例
            scale_x = original_img.width() / scene_rect.width()
            scale_y = original_img.height() / scene_rect.height()
            
            # 计算实际裁剪区域
            crop_x = self.selected_crop_rect.x() * scale_x
            crop_y = self.selected_crop_rect.y() * scale_y
            crop_w = self.selected_crop_rect.width() * scale_x
            crop_h = self.selected_crop_rect.height() * scale_y
            
            # 裁剪图片
            cropped_img = original_img.copy(QRectF(crop_x, crop_y, crop_w, crop_h).toRect())
            
            # 保存裁剪后的图片
            name, ext = os.path.splitext(os.path.basename(wallpaper_info["path"]))
            cache_filename = f"cropped_{name}{ext}"
            cache_path = os.path.join(self.manager.config.CACHE_DIR, cache_filename)
            cropped_img.save(cache_path)
            
            # 获取屏幕分辨率
            screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height
            
            # 调整图片适配屏幕
            final_filename = f"fit_{name}{ext}"
            final_cache_path = os.path.join(self.manager.config.CACHE_DIR, final_filename)
            
            # 根据需要缩小或放大图片
            if cropped_img.width() > 2*screen_width or cropped_img.height() > 2*screen_height:
                # 缩小
                self.image_utils.fit_image_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            elif cropped_img.width() < screen_width or cropped_img.height() < screen_height:
                # 放大，使用realesrgan
                self.realesrgan.fit_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            else:
                # 尺寸合适，直接保存
                cropped_img.save(final_cache_path)
            
            # 更新索引
            self.manager.update_crop_region(filename, [crop_x, crop_y, crop_w, crop_h], final_filename)
            
            # 设置为壁纸
            self.manager.set_wallpaper(final_cache_path, async_mode=False)
            
            # 清除选择
            self.selected_crop_rect = None
            self.image_view.crop_rect_item = None
            self.image_view.scene.update()
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "成功", "裁剪并设置壁纸成功!")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"裁剪失败: {str(e)}")
    
    def exclude_wallpaper(self):
        """排除当前壁纸"""
        if not self.wallpaper_list:
            return
            
        filename = self.wallpaper_list[self.current_index]
        self.excluded_files.add(filename)
        self.file_utils.add_to_excluded(filename)
        self.wallpaper_list.remove(filename)
        
        if self.wallpaper_list:
            self.current_index = self.current_index % len(self.wallpaper_list)
            self.load_wallpaper()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "没有更多壁纸了!")
    
    def refresh_index(self):
        """刷新索引"""
        if not self.rebuild_index():
            return
            
        self.initialize_data()
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "完成", f"索引已刷新! 找到 {len(self.wallpaper_list)} 张可用壁纸")