DARK_THEME = """
    QMainWindow {
        background-color: #202020;
    }
    QWidget {
        font-family: 'Segoe UI', sans-serif;
        font-size: 11pt;
        color: #E0E0E0;
    }
    
    /* 应用标题 */
    #appTitle {
        font-size: 14pt;
        font-weight: 500;
        color: #F0F0F0;
    }
    
    /* 分割线 */
    #divider {
        color: #404040;
        max-height: 1px;
    }
    
    /* 顶部栏 */
    #topBar {
        background-color: #202020;
        border: none;
        min-height: 40px;
    }
    
    /* 底部栏 */
    #bottomBar {
        background-color: #202020;
        border: none;
        min-height: 50px;
    }
    
    /* 图像视图 */
    #imageView {
        background-color: #303030;
        border: 1px solid #404040;
        border-radius: 8px;
    }
    
    /* 基本按钮样式 */
    QPushButton {
        background-color: #333333;
        border: 1px solid #454545;
        border-radius: 5px;
        padding: 8px 16px;
        min-width: 80px;
        color: #E0E0E0;
    }
    
    QPushButton:hover {
        background-color: #404040;
        border-color: #505050;
    }
    
    QPushButton:pressed {
        background-color: #505050;
        border-color: #606060;
    }
    
    /* 工具按钮 */
    QPushButton[class="tool-button"] {
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        min-width: 60px;
    }
    
    QPushButton[class="tool-button"]:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    QPushButton[class="tool-button"]:pressed {
        background-color: rgba(255, 255, 255, 0.08);
    }
    
    /* 突出按钮 */
    QPushButton[class="accent-button"] {
        background-color: #192C45;
        color: #60A5FA;
        border: 1px solid #2859A8;
        font-weight: 500;
    }
    
    QPushButton[class="accent-button"]:hover {
        background-color: #1F375D;
    }
    
    QPushButton[class="accent-button"]:pressed {
        background-color: #264573;
    }
    
    /* 操作按钮 */
    QPushButton[class="action-button"] {
        background-color: #333333;
        color: #C0C0C0;
        border: 1px solid #454545;
    }
    
    QPushButton[class="action-button"]:hover {
        background-color: #404040;
        border-color: #505050;
    }
    
    /* 主要按钮 */
    QPushButton[class="primary-button"] {
        background-color: #0078D7;
        color: white;
        border: none;
        font-weight: 500;
    }
    
    QPushButton[class="primary-button"]:hover {
        background-color: #1683D9;
    }
    
    QPushButton[class="primary-button"]:pressed {
        background-color: #106EBE;
    }
    
    /* 状态栏 */
    QStatusBar {
        background-color: #252525;
        color: #B0B0B0;
        border-top: 1px solid #353535;
    }
    
    /* 其他控件样式保持不变... */
"""