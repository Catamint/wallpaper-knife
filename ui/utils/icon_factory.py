from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
import os

class IconFactory:
    """图标工厂，支持深浅主题"""
    
    def __init__(self, icon_dir="icons"):
        """
        初始化图标工厂
        
        Args:
            icon_dir: 图标目录路径
        """
        # 确定图标目录路径
        import os
        this_file = os.path.abspath(__file__)
        ui_dir = os.path.dirname(os.path.dirname(this_file))
        app_dir = os.path.dirname(ui_dir)
        
        self.icon_dir = os.path.join(app_dir, icon_dir)
        os.makedirs(self.icon_dir, exist_ok=True)
        
        # 缓存图标
        self.icon_cache = {}
        
    def get_icon(self, name, dark_mode=False):
        """
        获取图标，支持深色和浅色主题
        
        Args:
            name: 图标名称（不包括扩展名）
            dark_mode: 是否为深色模式
        
        Returns:
            QIcon: 图标对象
        """
        # 缓存键
        cache_key = f"{name}_{'dark' if dark_mode else 'light'}"
        
        # 如果已缓存，直接返回
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # 尝试加载特定主题的图标
        theme_suffix = "_dark" if dark_mode else "_light"
        theme_path = os.path.join(self.icon_dir, f"{name}{theme_suffix}.png")
        
        # 如果存在主题特定图标，直接加载
        if os.path.exists(theme_path):
            icon = QIcon(theme_path)
            self.icon_cache[cache_key] = icon
            return icon
            
        # 否则尝试加载通用图标
        general_path = os.path.join(self.icon_dir, f"{name}.png")
        if os.path.exists(general_path):
            # 对于深色主题，可能需要反转颜色
            if dark_mode:
                icon = self._create_inverted_icon(general_path)
            else:
                icon = QIcon(general_path)
                
            self.icon_cache[cache_key] = icon
            return icon
        
        # 如果都不存在，返回空图标
        print(f"警告: 找不到图标 {name}")
        return QIcon()
        
    def _create_inverted_icon(self, path):
        """为深色主题创建反色图标"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return QIcon()
            
        inverted = QPixmap(pixmap.size())
        inverted.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(inverted)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return QIcon(inverted)
    
    def get_all_icons(self):
        """获取所有可用的图标名称"""
        icons = []
        for file in os.listdir(self.icon_dir):
            if file.endswith(".png"):
                name = os.path.splitext(file)[0]
                # 移除主题后缀
                name = name.replace("_dark", "").replace("_light", "")
                if name not in icons:
                    icons.append(name)
        return icons