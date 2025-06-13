LIGHT_THEME = """
    QMainWindow {
        background-color: #FAFAFA;
    }
    QWidget {
        font-family: 'Segoe UI', sans-serif;
        font-size: 11pt;
        color: #202020;
    }
    
    /* 应用标题 */
    #appTitle {
        font-size: 14pt;
        font-weight: 500;
        color: #202020;
    }
    
    /* 分割线 */
    #divider {
        color: #E0E0E0;
        max-height: 1px;
    }
    
    /* 顶部栏 */
    #topBar {
        background-color: #FAFAFA;
        border: none;
        min-height: 40px;
    }
    
    /* 底部栏 */
    #bottomBar {
        background-color: #FAFAFA;
        border: none;
        min-height: 50px;
    }
    
    /* 图像视图 */
    #imageView {
        background-color: #F0F0F0;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }
    
    /* 基本按钮样式 */
    QPushButton {
        background-color: #F3F3F3;
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        padding: 8px 16px;
        min-width: 80px;
        color: #202020;
    }
    
    QPushButton:hover {
        background-color: #EAEAEA;
        border-color: #D0D0D0;
    }
    
    QPushButton:pressed {
        background-color: #E0E0E0;
        border-color: #C0C0C0;
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
        background-color: rgba(0, 0, 0, 0.05);
    }
    
    QPushButton[class="tool-button"]:pressed {
        background-color: rgba(0, 0, 0, 0.08);
    }
    
    /* 突出按钮 */
    QPushButton[class="accent-button"] {
        background-color: #E8F0FE;
        color: #0078D7;
        border: 1px solid #0078D7;
        font-weight: 500;
    }
    
    QPushButton[class="accent-button"]:hover {
        background-color: #D5E4F9;
    }
    
    QPushButton[class="accent-button"]:pressed {
        background-color: #BDD8F6;
    }
    
    /* 操作按钮 */
    QPushButton[class="action-button"] {
        background-color: #F3F3F3;
        color: #505050;
        border: 1px solid #D0D0D0;
    }
    
    QPushButton[class="action-button"]:hover {
        background-color: #EAEAEA;
        border-color: #C0C0C0;
    }
    
    /* 主要按钮 */
    QPushButton[class="primary-button"] {
        background-color: #0078D7;
        color: white;
        border: none;
        font-weight: 500;
    }
    
    QPushButton[class="primary-button"]:hover {
        background-color: #006CC1;
    }
    
    QPushButton[class="primary-button"]:pressed {
        background-color: #005BA1;
    }
    
    /* 状态栏 */
    QStatusBar {
        background-color: #F5F5F5;
        color: #505050;
        border-top: 1px solid #E0E0E0;
    }
    
    /* 其他控件样式保持不变... */
"""