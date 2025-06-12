DARK_THEME = """
    QMainWindow, QWidget {
        background-color: #202020;
        color: #e0e0e0;
    }
    QPushButton {
        background-color: #323232;
        border: 1px solid #505050;
        border-radius: 5px;
        padding: 8px 16px;
        min-width: 80px;
        color: #e0e0e0;
    }
    QPushButton:hover {
        background-color: #404040;
    }
    QPushButton:pressed {
        background-color: #505050;
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
        border: 1px solid #505050;
        border-radius: 3px;
        background-color: #323232;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #0078d4;
        border-radius: 2px;
    }
    QStatusBar {
        background-color: #303030;
        color: #b0b0b0;
    }
"""