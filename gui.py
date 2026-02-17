from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QSlider, 
                             QHBoxLayout, QMessageBox, QComboBox, QFrame,
                             QGraphicsDropShadowEffect, QScrollArea)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
import asyncio
import qasync

# Modern Discord Colors (2024/2025 Palette)
DISCORD_BG = "#313338"       # Main background
DISCORD_CARD = "#2b2d31"     # Card/Panel background
DISCORD_INPUT = "#1e1f22"    # Input field background
DISCORD_TEXT = "#dbdee1"     # Main text
DISCORD_HEADER = "#f2f3f5"   # Headers
DISCORD_BLURPLE = "#5865F2"  # Brand color
DISCORD_BLURPLE_HOVER = "#4752C4"
DISCORD_RED = "#da373c"      # Destructive
DISCORD_RED_HOVER = "#a1282c"
DISCORD_GREEN = "#23a559"    # Success
DISCORD_GREEN_HOVER = "#1a7f42"
DISCORD_SUBTEXT = "#949ba4"  # Placeholders/Sublabels

class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {DISCORD_CARD};
                border-radius: 8px;
            }}
        """)

class MainWindow(QMainWindow):
    def __init__(self, discord_client, audio_handler):
        super().__init__()
        self.discord_client = discord_client
        self.audio_handler = audio_handler
        
        self.setWindowTitle("Discord Voice Booster")
        self.setGeometry(100, 100, 440, 800) 
        
        # Global Stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {DISCORD_BG}; }}
            QWidget {{ font-family: 'Segoe UI', 'gg sans', sans-serif; font-size: 14px; color: {DISCORD_TEXT}; }}
            QScrollArea {{ border: none; background-color: {DISCORD_BG}; }}
            QScrollBar:vertical {{
                border: none;
                background: {DISCORD_BG};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {DISCORD_INPUT};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}

            QLabel {{ font-weight: 500; }}
            QLabel#Header {{ color: {DISCORD_HEADER}; font-size: 20px; font-weight: bold; margin-bottom: 5px; }}
            QLabel#SubHeader {{ color: {DISCORD_SUBTEXT}; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
            
            QLineEdit {{ 
                background-color: {DISCORD_INPUT}; 
                border: none; 
                border-radius: 4px; 
                padding: 12px; 
                color: {DISCORD_HEADER}; 
                font-size: 14px;
            }}
            QLineEdit:focus {{ color: {DISCORD_HEADER}; }}
            QLineEdit::placeholder {{ color: {DISCORD_SUBTEXT}; }}

            QComboBox {{
                background-color: {DISCORD_INPUT};
                border: none;
                border-radius: 4px;
                padding: 12px;
                color: {DISCORD_HEADER};
                selection-background-color: {DISCORD_INPUT};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {DISCORD_CARD};
                color: {DISCORD_TEXT};
                selection-background-color: {DISCORD_BLURPLE};
                border: 1px solid {DISCORD_BG};
            }}

            QSlider::groove:horizontal {{
                border: 1px solid {DISCORD_BG};
                height: 8px;
                background: {DISCORD_INPUT};
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {DISCORD_BLURPLE};
                border: 2px solid {DISCORD_BG};
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {DISCORD_HEADER};
            }}
            QSlider::sub-page:horizontal {{
                background: {DISCORD_BLURPLE};
                border-radius: 4px;
            }}
        """)

        # --- SCROLL AREA SETUP ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container Widget for Layout
        self.container_widget = QWidget()
        self.container_widget.setObjectName("Container")
        self.container_widget.setStyleSheet(f"QWidget#Container {{ background-color: {DISCORD_BG}; }}")
        
        main_layout = QVBoxLayout(self.container_widget)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(24, 32, 24, 32)
        self.main_layout = main_layout
        
        self.scroll_area.setWidget(self.container_widget)
        self.setCentralWidget(self.scroll_area)

        # === TITLE HEADER ===
        title_layout = QVBoxLayout()
        app_title = QLabel("Voice Booster")
        app_title.setObjectName("Header")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(app_title)
        
        status_sub = QLabel("Advanced Audio Injection")
        status_sub.setStyleSheet(f"color: {DISCORD_SUBTEXT}; font-size: 13px; font-weight: normal;")
        status_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(status_sub)
        
        main_layout.addLayout(title_layout)

        # === CARD 1: ACCOUNT ===
        account_card = ModernCard()
        acc_layout = QVBoxLayout(account_card)
        acc_layout.setSpacing(12)
        acc_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_token = QLabel("USER ACCOUNT")
        lbl_token.setObjectName("SubHeader")
        acc_layout.addWidget(lbl_token)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste User Token")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        acc_layout.addWidget(self.token_input)
        
        self.connect_btn = QPushButton("Login to Discord")
        self.style_button(self.connect_btn, DISCORD_BLURPLE, DISCORD_BLURPLE_HOVER)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setFixedHeight(38)
        acc_layout.addWidget(self.connect_btn)
        
        main_layout.addWidget(account_card)

        # === CARD 2: AUDIO CONFIG ===
        audio_card = ModernCard()
        aud_layout = QVBoxLayout(audio_card)
        aud_layout.setSpacing(16)
        aud_layout.setContentsMargins(16, 16, 16, 16)
        
        # Input Device
        dev_layout = QVBoxLayout()
        dev_layout.setSpacing(8)
        lbl_dev = QLabel("INPUT DEVICE")
        lbl_dev.setObjectName("SubHeader")
        dev_layout.addWidget(lbl_dev)
        
        self.device_combo = QComboBox()
        self.populate_devices()
        self.device_combo.currentIndexChanged.connect(self.change_device)
        dev_layout.addWidget(self.device_combo)
        aud_layout.addLayout(dev_layout)
        
        # Gain Slider
        gain_layout = QVBoxLayout()
        gain_layout.setSpacing(8)
        
        header_row = QHBoxLayout()
        lbl_gain = QLabel("MICROPHONE BOOST")
        lbl_gain.setObjectName("SubHeader")
        header_row.addWidget(lbl_gain)
        
        self.gain_val_label = QLabel("0 dB")
        self.gain_val_label.setStyleSheet(f"color: {DISCORD_HEADER}; font-weight: bold; font-size: 12px;")
        self.gain_val_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_row.addWidget(self.gain_val_label)
        
        gain_layout.addLayout(header_row)

        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setMinimum(0)
        self.gain_slider.setMaximum(200) # 200 dB Absolute Limit
        self.gain_slider.setValue(0)
        self.gain_slider.valueChanged.connect(self.update_gain)
        gain_layout.addWidget(self.gain_slider)
        
        aud_layout.addLayout(gain_layout)
        main_layout.addWidget(audio_card)

        # === CARD 3: EFFECTS (Pitch & EQ) ===
        effects_card = ModernCard()
        fx_layout = QVBoxLayout(effects_card)
        fx_layout.setSpacing(16)
        fx_layout.setContentsMargins(16, 16, 16, 16)

        # Pitch
        pitch_layout = QVBoxLayout()
        header_pitch_row = QHBoxLayout()
        lbl_pitch = QLabel("PITCH SHIFT")
        lbl_pitch.setObjectName("SubHeader")
        header_pitch_row.addWidget(lbl_pitch)
        
        self.pitch_val_label = QLabel("1.0x")
        self.pitch_val_label.setStyleSheet(f"color: {DISCORD_HEADER}; font-weight: bold; font-size: 12px;")
        self.pitch_val_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_pitch_row.addWidget(self.pitch_val_label)
        pitch_layout.addLayout(header_pitch_row)

        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setMinimum(50)  # 0.5x
        self.pitch_slider.setMaximum(200) # 2.0x
        self.pitch_slider.setValue(100)   # 1.0x
        self.pitch_slider.valueChanged.connect(self.update_pitch)
        pitch_layout.addWidget(self.pitch_slider)
        
        fx_layout.addLayout(pitch_layout)

        # EQ
        eq_group = QVBoxLayout()
        lbl_eq = QLabel("3-BAND EQUALIZER")
        lbl_eq.setObjectName("SubHeader")
        eq_group.addWidget(lbl_eq)

        eq_sliders_row = QHBoxLayout()
        
        # Helper to make vertical slider
        def create_eq_slider(label_text):
            v_layout = QVBoxLayout()
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {DISCORD_SUBTEXT}; font-size: 11px;")
            
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setMinimum(-20)
            slider.setMaximum(20)
            slider.setValue(0)
            slider.setFixedHeight(80) # compact
            slider.setStyleSheet(f"""
                QSlider::groove:vertical {{
                    background: {DISCORD_INPUT};
                    width: 6px;
                    border-radius: 3px;
                }}
                QSlider::handle:vertical {{
                    background: {DISCORD_BLURPLE};
                    height: 14px;
                    border-radius: 7px;
                    margin: 0 -4px;
                }}
                QSlider::sub-page:vertical {{
                    background: {DISCORD_INPUT};
                    border-radius: 3px;
                }}
                QSlider::add-page:vertical {{
                    background: {DISCORD_BLURPLE};
                    border-radius: 3px;
                }}
            """)
            
            val_label = QLabel("0")
            val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_label.setStyleSheet(f"color: {DISCORD_HEADER}; font-size: 10px;")
            
            v_layout.addWidget(val_label)
            v_layout.addWidget(slider)
            v_layout.addWidget(label)
            return v_layout, slider, val_label

        l_layout, self.eq_low, self.val_low = create_eq_slider("Low")
        m_layout, self.eq_mid, self.val_mid = create_eq_slider("Mid")
        h_layout, self.eq_high, self.val_high = create_eq_slider("High")
        
        self.eq_low.valueChanged.connect(self.update_eq)
        self.eq_mid.valueChanged.connect(self.update_eq)
        self.eq_high.valueChanged.connect(self.update_eq)

        eq_sliders_row.addLayout(l_layout)
        eq_sliders_row.addLayout(m_layout)
        eq_sliders_row.addLayout(h_layout)
        
        eq_group.addLayout(eq_sliders_row)
        fx_layout.addLayout(eq_group)
        
        main_layout.addWidget(effects_card)


        # === CARD 4: CONNECTION ===
        conn_card = ModernCard()
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setSpacing(12)
        conn_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_chan = QLabel("VOICE CHANNEL")
        lbl_chan.setObjectName("SubHeader")
        conn_layout.addWidget(lbl_chan)
        
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel ID")
        conn_layout.addWidget(self.channel_input)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        self.join_btn = QPushButton("Join Voice")
        self.style_button(self.join_btn, DISCORD_GREEN, DISCORD_GREEN_HOVER)
        self.join_btn.clicked.connect(self.join_channel)
        self.join_btn.setEnabled(False)
        self.join_btn.setFixedHeight(38)
        
        self.leave_btn = QPushButton("Disconnect")
        self.style_button(self.leave_btn, DISCORD_RED, DISCORD_RED_HOVER)
        self.leave_btn.clicked.connect(self.leave_channel)
        self.leave_btn.setEnabled(False)
        self.leave_btn.setFixedHeight(38)
        
        btn_row.addWidget(self.join_btn)
        btn_row.addWidget(self.leave_btn)
        conn_layout.addLayout(btn_row)
        
        main_layout.addWidget(conn_card)

        main_layout.addStretch()

    def style_button(self, button, color, hover_color):
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {color};
                margin-top: 1px;
            }}
            QPushButton:disabled {{
                background-color: {DISCORD_INPUT};
                color: {DISCORD_SUBTEXT};
            }}
        """)
        
    def show_error(self, title, message):
        """Safely show error message box without blocking the async loop directly."""
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, title, message))

    @qasync.asyncSlot()
    async def toggle_connection(self):
        if self.discord_client.is_ready():
            # Logout
            await self.discord_client.close()
            self.connect_btn.setText("Login to Discord")
            self.style_button(self.connect_btn, DISCORD_BLURPLE, DISCORD_BLURPLE_HOVER)
            self.token_input.setEnabled(True)
            self.join_btn.setEnabled(False)
            self.leave_btn.setEnabled(False)
        else:
            # Login
            token = self.token_input.text().strip()
            if not token:
                self.show_error("Error", "Please enter a token.")
                return 

            self.connect_btn.setText("Connecting...")
            self.connect_btn.setEnabled(False)
            self.token_input.setEnabled(False)

            try:
                # Start discord client as a background task
                self.client_task = asyncio.create_task(self.run_client_background(token))
                
                # Wait for ready or for the task to fail
                done, pending = await asyncio.wait(
                    [asyncio.create_task(self.discord_client.wait_until_ready()), self.client_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                if self.client_task in done:
                    # Task finished early, likely an error
                    exception = self.client_task.exception()
                    if exception:
                        raise exception
                
                if self.discord_client.is_ready():
                    self.on_login_success()
                else:
                    self.connect_btn.setText("Login to Discord")
                    self.connect_btn.setEnabled(True)
                    self.token_input.setEnabled(True)

            except Exception as e:
                 self.show_error("Login Error", f"Failed to login: {e}")
                 self.connect_btn.setText("Login to Discord")
                 self.connect_btn.setEnabled(True)
                 self.token_input.setEnabled(True)

    async def run_client_background(self, token):
        async with self.discord_client:
            await self.discord_client.start(token)

    def on_login_success(self):
        self.connect_btn.setText("Logout")
        self.connect_btn.setEnabled(True)
        self.style_button(self.connect_btn, DISCORD_CARD, "#232428") 
        self.connect_btn.setStyleSheet(self.connect_btn.styleSheet() + f"QPushButton {{ border: 1px solid {DISCORD_RED}; color: {DISCORD_RED}; }} QPushButton:hover {{ background-color: {DISCORD_RED}; color: white; }}")
        
        self.join_btn.setEnabled(True)
        QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", "Logged in successfully!"))


    @qasync.asyncSlot()
    async def join_channel(self):
        channel_id_str = self.channel_input.text().strip()
        if not channel_id_str.isdigit():
             self.show_error("Error", "Invalid Channel ID.")
             return
        
        self.join_btn.setEnabled(False)
        self.join_btn.setText("Joining...")
        try:
            await self.discord_client.join_channel(channel_id_str)
            # Check if join was successful
            if self.discord_client.vc and self.discord_client.vc.is_connected():
                 self.leave_btn.setEnabled(True)
                 self.join_btn.setText("Connected")
                 self.join_btn.setStyleSheet(f"background-color: {DISCORD_INPUT}; color: {DISCORD_GREEN}; border: 1px solid {DISCORD_GREEN};")
            else:
                 self.join_btn.setEnabled(True)
                 self.join_btn.setText("Join Voice")
                 self.show_error("Error", "Failed to connect (Unknown reason).")
        except Exception as e:
            self.join_btn.setEnabled(True)
            self.join_btn.setText("Join Voice")
            self.show_error("Join Error", f"Failed to join: {str(e)}")


    @qasync.asyncSlot()
    async def leave_channel(self):
        self.leave_btn.setEnabled(False)
        await self.discord_client.leave_channel()
        
        # Reset buttons
        self.join_btn.setEnabled(True)
        self.join_btn.setText("Join Voice")
        self.style_button(self.join_btn, DISCORD_GREEN, DISCORD_GREEN_HOVER)

    def update_gain(self):
        value = self.gain_slider.value()
        # Convert dB to linear gain: 10^(dB/20)
        gain_factor = 10 ** (value / 20.0)
        self.audio_handler.set_gain(gain_factor)
        
        color = DISCORD_HEADER
        if value > 60: color = "#f0b232" 
        if value > 100: color = DISCORD_RED
        
        self.gain_val_label.setText(f"{value} dB")
        self.gain_val_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")

    def update_pitch(self):
        # 50 to 200 -> 0.5x to 2.0x
        val = self.pitch_slider.value()
        factor = val / 100.0
        self.audio_handler.set_pitch(factor)
        self.pitch_val_label.setText(f"{factor:.1f}x")

    def update_eq(self):
        l = self.eq_low.value()
        m = self.eq_mid.value()
        h = self.eq_high.value()
        
        self.val_low.setText(str(l))
        self.val_mid.setText(str(m))
        self.val_high.setText(str(h))
        
        self.audio_handler.set_eq(l, m, h)

    def populate_devices(self):
        try:
            devices = self.audio_handler.get_input_devices()
            for index, name in devices:
                self.device_combo.addItem(name, index)
        except Exception as e:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Audio Error", f"Failed to list devices: {e}"))
            
    def change_device(self):
        index = self.device_combo.currentData()
        if index is not None:
            try:
                self.audio_handler.start_stream(device_index=index)
                print(f"Switched to device index: {index}")
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Audio Error", f"Failed to switch device: {e}"))
