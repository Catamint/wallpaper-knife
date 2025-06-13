LIGHT_THEME = """
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
        min-width: 40px;
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
"""