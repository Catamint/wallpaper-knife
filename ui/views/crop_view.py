from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QEvent
from PyQt6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainter, QMouseEvent
from screeninfo import get_monitors

class CropGraphicsView(QGraphicsView):
    """裁剪图片视图"""
    cropSelected = pyqtSignal(QRectF)
    
    # 交互模式
    MODE_NONE = 0
    MODE_DRAW = 1
    MODE_MOVE = 2
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置为可交互
        self.setMouseTracking(True)
        self.setInteractive(True)
        
        # 裁剪相关变量
        self.start_point = None
        self.current_rect = None
        self.crop_rect_item = None
        self.overlay_item = None
        self.mode = self.MODE_NONE
        
        # 移动模式变量
        self.move_start_point = None
        self.rect_start_pos = None
        
        # 获取屏幕比例
        self.screen_ratio = 16/9  # 默认值
        try:
            monitors = get_monitors()
            if monitors:
                main_monitor = monitors[0]
                self.screen_ratio = main_monitor.width / main_monitor.height
        except Exception:
            pass  # 使用默认比例
        
        # 设置鼠标样式
        self.setCursor(Qt.CursorShape.CrossCursor)
    
    def setImage(self, pixmap):
        """设置图片"""
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        
        # 使用浮点数创建 QRectF
        rect = pixmap.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        scene_rect = QRectF(float(x), float(y), float(w), float(h))
        self.scene.setSceneRect(scene_rect)
        
        # 重置裁剪相关变量
        self.start_point = None
        self.current_rect = None
        self.crop_rect_item = None
        self.overlay_item = None
        self.mode = self.MODE_NONE
        
        # 添加全屏遮罩 (最初是全透明的)
        self.overlay_item = QGraphicsPathItem()
        self.overlay_item.setZValue(10)  # 确保在图片上方
        overlay_path = QPainterPath()
        overlay_path.addRect(scene_rect)
        self.overlay_item.setPath(overlay_path)
        
        # 设置遮罩为完全透明
        transparent_brush = QBrush(QColor(0, 0, 0, 0))
        self.overlay_item.setBrush(transparent_brush)
        
        # 设置边框为透明
        pen = QPen()
        pen.setStyle(Qt.PenStyle.NoPen)
        self.overlay_item.setPen(pen)
        
        self.scene.addItem(self.overlay_item)
        
        self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    def resizeEvent(self, event):
        """窗口大小变化时，调整图像大小"""
        if self.scene and self.scene.sceneRect().isValid():
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)
    
    def isInsideCropRect(self, point):
        """检查点是否在裁剪矩形内"""
        if self.current_rect:
            return self.current_rect.contains(point)
        return False
    
    def mousePressEvent(self, event):
        """鼠标按下事件处理"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            # 检查是否在现有裁剪矩形内
            if self.current_rect and self.isInsideCropRect(scene_pos):
                # 进入移动模式
                self.mode = self.MODE_MOVE
                self.move_start_point = scene_pos
                self.rect_start_pos = QPointF(self.current_rect.x(), self.current_rect.y())
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                # 进入绘制模式 - 清除旧矩形并开始新绘制
                self.clearCropRect()
                self.mode = self.MODE_DRAW
                self.start_point = scene_pos
                
                # 创建新矩形
                self.crop_rect_item = QGraphicsRectItem()
                pen = QPen(QColor(255, 255, 255))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                self.crop_rect_item.setPen(pen)
                self.crop_rect_item.setZValue(20)  # 确保在遮罩上方
                self.scene.addItem(self.crop_rect_item)
                self.setCursor(Qt.CursorShape.CrossCursor)
        elif event.button() == Qt.MouseButton.MiddleButton:
            # 中键拖动
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            # 创建假的左键点击事件来触发拖动
            fake_event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                event.pos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件处理"""
        scene_pos = self.mapToScene(event.pos())
        
        # 根据不同模式处理鼠标移动
        if self.mode == self.MODE_MOVE and event.buttons() & Qt.MouseButton.LeftButton:
            # 移动模式 - 移动裁剪矩形
            delta = scene_pos - self.move_start_point
            new_x = self.rect_start_pos.x() + delta.x()
            new_y = self.rect_start_pos.y() + delta.y()
            
            # 确保矩形不超出场景边界
            scene_rect = self.scene.sceneRect()
            rect_width = self.current_rect.width()
            rect_height = self.current_rect.height()
            
            new_x = max(scene_rect.left(), min(new_x, scene_rect.right() - rect_width))
            new_y = max(scene_rect.top(), min(new_y, scene_rect.bottom() - rect_height))
            
            # 更新矩形位置
            new_rect = QRectF(new_x, new_y, rect_width, rect_height)
            self.crop_rect_item.setRect(new_rect)
            self.current_rect = new_rect
            
            # 更新遮罩
            self._updateOverlay()
            
        elif self.mode == self.MODE_DRAW and self.start_point:
            # 绘制模式 - 创建/更新裁剪矩形
            # 计算矩形 (保持屏幕比例)
            raw_width = scene_pos.x() - self.start_point.x()
            raw_height = scene_pos.y() - self.start_point.y()
            
            # 确定方向
            sign_x = 1 if raw_width >= 0 else -1
            sign_y = 1 if raw_height >= 0 else -1
            
            # 计算等比例尺寸
            if abs(raw_width / self.screen_ratio) > abs(raw_height):
                # 以宽度为基准
                width = abs(raw_width)
                height = width / self.screen_ratio
            else:
                # 以高度为基准
                height = abs(raw_height)
                width = height * self.screen_ratio
                
            # 应用方向
            width *= sign_x
            height *= sign_y
            
            # 创建矩形
            rect = QRectF(
                self.start_point.x(),
                self.start_point.y(),
                width,
                height
            ).normalized()
            
            # 更新矩形
            if self.crop_rect_item:
                self.crop_rect_item.setRect(rect)
                self.current_rect = rect
                
                # 更新遮罩
                self._updateOverlay()
        
        elif not event.buttons() and self.current_rect:
            # 悬停模式 - 根据位置更新光标
            if self.isInsideCropRect(scene_pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
    
    def _updateOverlay(self):
        """更新遮罩效果 - 矩形内透明，外部半透明"""
        if self.overlay_item and self.current_rect:
            scene_rect = self.scene.sceneRect()
            overlay_path = QPainterPath()
            overlay_path.addRect(scene_rect)
            inner_path = QPainterPath()
            inner_path.addRect(self.current_rect)
            overlay_path = overlay_path.subtracted(inner_path)
            
            self.overlay_item.setPath(overlay_path)
            self.overlay_item.setBrush(QBrush(QColor(0, 0, 0, 120)))  # 半透明黑色
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == self.MODE_DRAW:
                # 绘制模式结束
                if self.current_rect and self.current_rect.width() > 10 and self.current_rect.height() > 10:
                    self.cropSelected.emit(self.current_rect)
            
            # 重置模式
            self.mode = self.MODE_NONE
            
            # 根据当前鼠标位置设置光标
            scene_pos = self.mapToScene(event.pos())
            if self.isInsideCropRect(scene_pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        elif event.button() == Qt.MouseButton.MiddleButton:
            # 中键松开时，创建假的左键松开事件
            fake_event = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                event.pos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            super().mouseReleaseEvent(fake_event)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            super().mouseReleaseEvent(event)
    
    def clearCropRect(self):
        """清除裁剪矩形"""
        if self.crop_rect_item:
            self.scene.removeItem(self.crop_rect_item)
            self.crop_rect_item = None
        
        # 重置遮罩为全透明
        if self.overlay_item:
            scene_rect = self.scene.sceneRect()
            overlay_path = QPainterPath()
            overlay_path.addRect(scene_rect)
            self.overlay_item.setPath(overlay_path)
            self.overlay_item.setBrush(QBrush(QColor(0, 0, 0, 0)))
        
        self.start_point = None
        self.current_rect = None
        self.mode = self.MODE_NONE
        self.setCursor(Qt.CursorShape.CrossCursor)
    
    def getCropRect(self):
        """获取裁剪矩形"""
        return self.current_rect
    
    def wheelEvent(self, event):
        """滚轮事件：缩放图片"""
        factor = 1.1
        if event.angleDelta().y() < 0:
            factor = 0.9
            
        self.scale(factor, factor)