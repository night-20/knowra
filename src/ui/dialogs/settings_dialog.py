from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
import keyring
from src.ui.widgets.toast import ToastNotification

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("偏好设置")
        self.setFixedSize(400, 200)
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title_lbl = QLabel("大模型 API 设置")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_lbl)
        
        # API Key
        lbl = QLabel("LLM API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("例如 sk-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        
        layout.addWidget(lbl)
        layout.addWidget(self.api_key_input)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self._save_settings)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setProperty("class", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_settings(self):
        try:
            key = keyring.get_password("Knowra", "api_key")
            if key:
                self.api_key_input.setText(key)
        except Exception:
            pass
            
    def _save_settings(self):
        key = self.api_key_input.text().strip()
        if key:
            try:
                keyring.set_password("Knowra", "api_key", key)
                ToastNotification.show_toast("API Key 已成功保存", "success")
                self.accept()
            except Exception as e:
                ToastNotification.show_toast(f"保存加密失败: {e}", "error")
        else:
            self.accept()
