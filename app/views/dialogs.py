from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt

class ProgressDialog(QDialog):
    """进度对话框"""
    def __init__(self, parent=None, title="处理中", message="请稍候..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        
        self.progress_label = QLabel("准备中...")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
    
    def update_progress(self, current, total, text):
        """更新进度"""
        self.progress_bar.setValue(int(100 * current / max(1, total)))
        self.progress_label.setText(f"处理中: {current+1}/{total} - {text}")

def show_error(parent, title, message):
    """显示错误对话框"""
    QMessageBox.critical(parent, title, message)

def show_info(parent, title, message):
    """显示信息对话框"""
    QMessageBox.information(parent, title, message)

def show_warning(parent, title, message):
    """显示警告对话框"""
    QMessageBox.warning(parent, title, message)

def ask_question(parent, title, message):
    """显示询问对话框"""
    return QMessageBox.question(parent, title, message) == QMessageBox.StandardButton.Yes