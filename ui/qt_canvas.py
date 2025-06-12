from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
                            QSplitter, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                            QGraphicsPathItem)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QRectF, QPoint, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush, QPainterPath
from screeninfo import get_monitors
import sys
import os
import random

class ResizableCropItem(QGraphicsRectItem):
    """可调整大小的裁剪矩形"""
    
    # 拖动模式
    MODE_NONE = 0
    MODE_MOVE = 1
    MODE_RESIZE_TL = 2  # Top-Left
    MODE_RESIZE_TR = 3  # Top-Right
    MODE_RESIZE_BL = 4  # Bottom-Left
    MODE_RESIZE_BR = 5  # Bottom-Right
    
    HANDLE_SIZE = 10.0
    
    def __init__(self, screen_ratio=16/9):
        super().__init__(0, 0, 200, 200)
        self.screen_ratio = screen_ratio  # 屏幕比例
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # 设置外观
        self.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine))
        
        # 创建遮罩
        self.overlay = QGraphicsPathItem(self)
        self.updateOverlay()
        
        # 拖动状态
        self.mode = self.MODE_NONE
        self.mouseStartPos = QPointF()
        self.rectStartPos = QPointF()
        self.rectStartSize = QPointF()
        
    def updateRect(self, rect):
        """更新矩形但保持比例"""
        self.setRect(rect)
        self.updateOverlay()
        
    def updateOverlay(self):
        """更新灰色遮罩"""
        rect = self.rect()
        
        # 创建一个覆盖整个场景的路径
        scene_rect = self.scene().sceneRect()
        overlay_path = QPainterPath()
        overlay_path.addRect(scene_rect)
        
        # 从路径中减去裁剪矩形
        inner_path = QPainterPath()
        inner_path.addRect(rect)
        overlay_path = overlay_path.subtracted(inner_path)
        
        # 设置遮罩路径
        self.overlay.setPath(overlay_path)
        self.overlay.setBrush(QBrush(QColor(0, 0, 0, 128)))
        self.overlay.setPen(Qt.PenStyle.NoPen)
        
    def handleAt(self, point):
        """检测鼠标是否在调整手柄上"""
        rect = self.rect()
        handle_size = self.HANDLE_SIZE
        
        # 调整手柄的矩形区域
        tl_rect = QRectF(rect.left() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size)
        tr_rect = QRectF(rect.right() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size)
        bl_rect = QRectF(rect.left() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        br_rect = QRectF(rect.right() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        
        if tl_rect.contains(point):
            return self.MODE_RESIZE_TL
        elif tr_rect.contains(point):
            return self.MODE_RESIZE_TR
        elif bl_rect.contains(point):
            return self.MODE_RESIZE_BL
        elif br_rect.contains(point):
            return self.MODE_RESIZE_BR
        
        # 如果在矩形内，则为移动模式
        if self.rect().contains(point):
            return self.MODE_MOVE
            
        return self.MODE_NONE
        
    def mousePressEvent(self, event):
        """鼠标按下"""
        self.mouseStartPos = event.pos()
        self.rectStartPos = self.rect().topLeft()
        self.rectStartSize = QPointF(self.rect().width(), self.rect().height())
        self.mode = self.handleAt(event.pos())
        
        # 如果点击在控制点或矩形上，我们自己处理
        if self.mode != self.MODE_NONE:
            return
            
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.mode == self.MODE_NONE:
            super().mouseMoveEvent(event)
            return
            
        # 鼠标移动的距离
        delta = event.pos() - self.mouseStartPos
        
        # 当前矩形
        rect = self.rect()
        
        if self.mode == self.MODE_MOVE:
            # 移动模式 - 移动整个矩形
            new_pos = self.rectStartPos + delta
            
            # 确保矩形在场景内
            scene_rect = self.scene().sceneRect()
            if new_pos.x() < scene_rect.left():
                new_pos.setX(scene_rect.left())
            if new_pos.y() < scene_rect.top():
                new_pos.setY(scene_rect.top())
            if new_pos.x() + rect.width() > scene_rect.right():
                new_pos.setX(scene_rect.right() - rect.width())
            if new_pos.y() + rect.height() > scene_rect.bottom():
                new_pos.setY(scene_rect.bottom() - rect.height())
                
            self.setRect(QRectF(new_pos, rect.size()))
            
        else:
            # 调整大小模式
            new_rect = QRectF(rect)
            
            # 根据屏幕比例计算新尺寸
            if self.mode == self.MODE_RESIZE_BR:
                # 右下角调整 - 简单地改变宽度，高度按比例调整
                new_width = self.rectStartSize.x() + delta.x()
                new_height = new_width / self.screen_ratio
                new_rect.setWidth(new_width)
                new_rect.setHeight(new_height)
                
            elif self.mode == self.MODE_RESIZE_BL:
                # 左下角调整
                new_width = self.rectStartSize.x() - delta.x()
                new_height = new_width / self.screen_ratio
                new_rect.setLeft(self.rectStartPos.x() + delta.x())
                new_rect.setHeight(new_height)
                
            elif self.mode == self.MODE_RESIZE_TR:
                # 右上角调整
                new_width = self.rectStartSize.x() + delta.x()
                new_height = new_width / self.screen_ratio
                new_rect.setTop(self.rectStartPos.y() + (self.rectStartSize.y() - new_height))
                new_rect.setWidth(new_width)
                
            elif self.mode == self.MODE_RESIZE_TL:
                # 左上角调整
                new_width = self.rectStartSize.x() - delta.x()
                new_height = new_width / self.screen_ratio
                new_rect.setLeft(self.rectStartPos.x() + delta.x())
                new_rect.setTop(self.rectStartPos.y() + (self.rectStartSize.y() - new_height))
            
            # 确保尺寸合理 - 不要太小
            if new_rect.width() < 50:
                return
                
            # 确保矩形在场景内
            scene_rect = self.scene().sceneRect()
            if new_rect.left() < scene_rect.left():
                return
            if new_rect.top() < scene_rect.top():
                return
            if new_rect.right() > scene_rect.right():
                return
            if new_rect.bottom() > scene_rect.bottom():
                return
                
            self.setRect(new_rect)
        
        self.updateOverlay()
        
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self.mode = self.MODE_NONE
        super().mouseReleaseEvent(event)
        
    def paint(self, painter, option, widget):
        """绘制矩形和控制点"""
        # 绘制主矩形框
        super().paint(painter, option, widget)
        
        # 绘制调整手柄
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        rect = self.rect()
        handle_size = self.HANDLE_SIZE
        
        # 四个角的手柄
        handle_rects = [
            QRectF(rect.left() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size),
            QRectF(rect.right() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size),
            QRectF(rect.left() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size),
            QRectF(rect.right() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        ]
        
        for handle_rect in handle_rects:
            painter.drawRect(handle_rect)


class CropGraphicsView(QGraphicsView):
    """裁剪图片视图"""
    cropSelected = pyqtSignal(QRectF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置为可交互
        self.setMouseTracking(True)
        self.setInteractive(True)
        
        # 裁剪矩形
        self.crop_item = None
        self.screen_ratio = 16/9  # 默认屏幕比例
        
        # 尝试获取实际屏幕比例
        try:
            monitors = get_monitors()
            if monitors:
                main_monitor = monitors[0]
                self.screen_ratio = main_monitor.width / main_monitor.height
        except Exception:
            pass  # 使用默认比例
    
    def setImage(self, pixmap):
        """设置图片"""
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        
        # 使用浮点数创建 QRectF
        rect = pixmap.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        scene_rect = QRectF(float(x), float(y), float(w), float(h))
        self.scene.setSceneRect(scene_rect)
        
        # 创建并添加裁剪矩形
        # 计算一个合理的初始裁剪大小（场景的60%宽度）
        initial_width = scene_rect.width() * 0.6
        initial_height = initial_width / self.screen_ratio
        
        # 居中放置
        x = (scene_rect.width() - initial_width) / 2
        y = (scene_rect.height() - initial_height) / 2
        
        # 创建裁剪矩形
        self.crop_item = ResizableCropItem(self.screen_ratio)
        self.crop_item.setRect(QRectF(x, y, initial_width, initial_height))
        self.scene.addItem(self.crop_item)
        
        self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    def resizeEvent(self, event):
        """窗口大小变化时，调整图像大小"""
        if self.scene and self.scene.items():
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)
    
    def getCropRect(self):
        """获取裁剪矩形"""
        if self.crop_item:
            return self.crop_item.rect()
        return None