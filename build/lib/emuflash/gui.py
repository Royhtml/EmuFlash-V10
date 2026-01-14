import os
import shutil
import zipfile
import tempfile
import webbrowser
import subprocess
import platform
from datetime import datetime
import json
import threading
import time
from pathlib import Path
from PIL import Image
import pyttsx3  # TTS library

# PyQt5 imports
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton

class FlashGameManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.games_dir = "flash_games"
        self.data_file = "games_data.json"
        self.current_game = None
        self.setWindowIcon(QIcon("icon/icon.ico"))
        self.emulator_process = None
        self.game_data = self.load_game_data()
        self.cover_size = (300, 200)  # Default cover size
        self.tray_icon = None
        self.tts_engine = None
        self.tts_enabled = True
        self.current_language = "english"  # "english" or "chinese"
        
        # Initialize TTS
        self.init_tts()
        
        # Language dictionaries
        self.languages = {
            "english": self.get_english_strings(),
            "chinese": self.get_chinese_strings()
        }
        
        self.setup_ui()
        self.setup_system_tray()
        self.load_games()
        self.show_minimized_start = False  # Flag untuk start minimized
        
    def init_tts(self):
        """Initialize Text-to-Speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            # Set female voice with soft tone
            voices = self.tts_engine.getProperty('voices')
            
            # Priority: female voices in both languages
            female_voices = []
            for voice in voices:
                # Look for female voices
                if 'female' in voice.name.lower():
                    female_voices.append(voice)
                # Also check for soft-sounding voices
                elif 'zira' in voice.name.lower():  # Microsoft Zira is a good female voice
                    female_voices.append(voice)
                elif 'hazel' in voice.name.lower():  # Microsoft Hazel (female)
                    female_voices.append(voice)
            
            if female_voices:
                # Choose the best female voice
                self.tts_engine.setProperty('voice', female_voices[0].id)
            else:
                # Fallback to any available voice
                for voice in voices:
                    if 'english' in voice.name.lower() or 'chinese' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Set softer speech properties
            self.tts_engine.setProperty('rate', 130)  # Slower for softer tone
            self.tts_engine.setProperty('volume', 0.7)  # Lower volume for softer tone
            
            # Try to set pitch if supported
            try:
                self.tts_engine.setProperty('pitch', 1.2)  # Higher pitch for female voice
            except:
                pass
                
        except Exception as e:
            print(f"TTS initialization error: {e}")
            self.tts_enabled = False
            
    def speak(self, text):
        """Speak text using TTS"""
        if self.tts_enabled and self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
                
    def format_game_name_for_speech(self, game_name):
        """Format game name for TTS - remove underscores and file extensions"""
        # Remove file extension
        if '.' in game_name:
            game_name = game_name.rsplit('.', 1)[0]
        
        # Replace underscores with spaces
        game_name = game_name.replace('_', ' ')
        
        # Remove common file patterns
        game_name = game_name.replace('.swf', '').replace('.zip', '')
        
        return game_name
    
    def speak_game_start(self, game_name):
        """Speak game start message"""
        if self.tts_enabled and self.tts_engine:
            formatted_name = self.format_game_name_for_speech(game_name)
            
            if self.current_language == "english":
                message = f"The game {formatted_name} was successfully run. It is hoped that it will maintain good playing time."
            else:
                message = f"游戏 {formatted_name} 已成功运行。希望您保持良好的游戏时间。"
            
            self.speak(message)
                
    def get_english_strings(self):
        """Return English language strings"""
        return {
            "app_title": "EmuFlash Manager",
            "select_game": "🎮 Select a game to play",
            "status_ready": "Ready. Total games: {0}",
            "status_upload_success": "✅ {0} games uploaded successfully!",
            "upload_button": "📤 Upload",
            "extract_button": "📁 Extract",
            "rename_button": "✏️ Rename",
            "delete_button": "🗑️ Delete",
            "refresh_button": "🔄 Refresh",
            "search_placeholder": "Search games...",
            "filter_categories": ["All", "Action", "Adventure", "Puzzle", "Arcade", 
                                  "Strategy", "Sport", "Uncategorized"],
            "games_list": "📁 Games List:",
            "cover_preview": "🖼️ Cover Preview",
            "edit_cover": "✏️ Edit Cover",
            "player_tab": "🎮 Player",
            "manual_tab": "📖 Manual",
            "stats_tab": "📊 Statistics",
            "info_tab": "🧑‍💻 Info",
            "game_controls": "🎛️ Game Controls",
            "play_button": "▶️ Play",
            "stop_button": "⏹️ Stop",
            "fullscreen_button": "🔲 Fullscreen",
            "game_details": "📝 Game Details",
            "edit_info": "✏️ Edit Info",
            "set_category": "📂 Category",
            "set_rating": "⭐ Rating",
            "take_screenshot": "📸 Screenshot",
            "volume": "Volume",
            "status_emulator_search": "Status: Searching for Flash Player Emulator...",
            "status_game_running": "Status: Game running with {0}",
            "status_game_stopped": "Status: Game stopped",
            "status_emulator_not_found": "Status: Emulator not found",
            "warning_select_game": "Warning: Please select a game first!",
            "confirm_delete": "Confirm Delete",
            "delete_message": "Are you sure you want to delete '{0}'?\n\nFile will be permanently deleted!",
            "tray_show_hide": "Show/Hide",
            "tray_play_last": "Play Last Game",
            "tray_recent_games": "Recent Games",
            "tray_exit": "Exit",
            "tray_notification": "EmuFlash Manager",
            "tray_app_running": "Application running in system tray",
            "tray_playing": "Playing: {0}",
            "manual_text": self.get_english_manual(),
            "info_text": self.get_english_info(),
            "language_menu": "🌐 Language",
            "tts_toggle": "🔊 TTS: ON",
            "tts_enable": "Enable TTS",
            "tts_disable": "Disable TTS",
            "tts_test": "Test TTS",
        }
        
    def get_chinese_strings(self):
        """Return Chinese language strings"""
        return {
            "app_title": "EmuFlash 管理器",
            "select_game": "🎮 选择要玩的游戏",
            "status_ready": "准备就绪。游戏总数：{0}",
            "status_upload_success": "✅ {0} 个游戏上传成功！",
            "upload_button": "📤 上传",
            "extract_button": "📁 解压",
            "rename_button": "✏️ 重命名",
            "delete_button": "🗑️ 删除",
            "refresh_button": "🔄 刷新",
            "search_placeholder": "搜索游戏...",
            "filter_categories": ["全部", "动作", "冒险", "解谜", "街机", 
                                  "策略", "体育", "未分类"],
            "games_list": "📁 游戏列表：",
            "cover_preview": "🖼️ 封面预览",
            "edit_cover": "✏️ 编辑封面",
            "player_tab": "🎮 播放器",
            "manual_tab": "📖 手册",
            "stats_tab": "📊 统计",
            "info_tab": "🧑‍💻 信息",
            "game_controls": "🎛️ 游戏控制",
            "play_button": "▶️ 播放",
            "stop_button": "⏹️ 停止",
            "fullscreen_button": "🔲 全屏",
            "game_details": "📝 游戏详情",
            "edit_info": "✏️ 编辑信息",
            "set_category": "📂 分类",
            "set_rating": "⭐ 评分",
            "take_screenshot": "📸 截图",
            "volume": "音量",
            "status_emulator_search": "状态：正在搜索Flash播放器模拟器...",
            "status_game_running": "状态：游戏正在使用 {0} 运行",
            "status_game_stopped": "状态：游戏已停止",
            "status_emulator_not_found": "状态：未找到模拟器",
            "warning_select_game": "警告：请先选择游戏！",
            "confirm_delete": "确认删除",
            "delete_message": "确定要删除 '{0}' 吗？\n\n文件将被永久删除！",
            "tray_show_hide": "显示/隐藏",
            "tray_play_last": "播放最后游戏",
            "tray_recent_games": "最近游戏",
            "tray_exit": "退出",
            "tray_notification": "EmuFlash 管理器",
            "tray_app_running": "应用程序在系统托盘中运行",
            "tray_playing": "正在播放：{0}",
            "manual_text": self.get_chinese_manual(),
            "info_text": self.get_chinese_info(),
            "language_menu": "🌐 语言",
            "tts_toggle": "🔊 语音: 开",
            "tts_enable": "启用语音",
            "tts_disable": "禁用语音",
            "tts_test": "测试语音",
        }
        
    def get_english_manual(self):
        """Return English manual text"""
        return """
        <h3>🎮 General Flash Game Controls:</h3>
        <ul>
        <li><b>Double Click</b> on game card to play immediately</li>
        <li><b>Right Click</b> on game card for quick menu</li>
        <li><b>Arrow Left/Right</b>: Move left/right</li>
        <li><b>Arrow Up/Down</b>: Jump/crouch</li>
        <li><b>Space</b>: Main action (shoot/jump)</li>
        <li><b>Enter</b>: Pause/Menu</li>
        <li><b>ESC</b>: Exit game</li>
        <li><b>Z/X/C</b>: Additional action buttons</li>
        <li><b>Ctrl+R</b>: Restart game</li>
        <li><b>Ctrl+T</b>: Minimize to tray</li>
        </ul>
        
        <h3>⚙️ System Tray Information:</h3>
        <ul>
        <li><b>Double Click</b> tray icon: Show/Hide window</li>
        <li><b>Middle Click</b> tray icon: Play last game</li>
        <li><b>Right Click</b> tray icon: Application menu</li>
        <li>Recent games appear in tray menu</li>
        </ul>
        """
        
    def get_chinese_manual(self):
        """Return Chinese manual text"""
        return """
        <h3>🎮 通用Flash游戏控制：</h3>
        <ul>
        <li><b>双击</b>游戏卡片立即播放</li>
        <li><b>右键单击</b>游戏卡片获取快速菜单</li>
        <li><b>左/右箭头</b>: 向左/右移动</li>
        <li><b>上/下箭头</b>: 跳跃/蹲下</li>
        <li><b>空格键</b>: 主要动作（射击/跳跃）</li>
        <li><b>回车键</b>: 暂停/菜单</li>
        <li><b>ESC键</b>: 退出游戏</li>
        <li><b>Z/X/C键</b>: 附加动作按钮</li>
        <li><b>Ctrl+R</b>: 重新开始游戏</li>
        <li><b>Ctrl+T</b>: 最小化到托盘</li>
        </ul>
        
        <h3>⚙️ 系统托盘信息：</h3>
        <ul>
        <li><b>双击</b>托盘图标：显示/隐藏窗口</li>
        <li><b>中键单击</b>托盘图标：播放最后游戏</li>
        <li><b>右键单击</b>托盘图标：应用程序菜单</li>
        <li>最近游戏出现在托盘菜单中</li>
        </ul>
        """
        
    def get_english_info(self):
        """Return English info text"""
        return """
        <h3>🧑‍💻 Developer Information:</h3>
        <ul>
        <li><b>EmuFlash Developer</b>: Dwi Bakti N Dev</li>
        <li><b>EmuFlash Manager</b>: Version 10.0.0</li>
        <li><b>Features</b>: Multi-language support, TTS, Game management</li>
        <li><b>Text-to-Speech</b>: Soft female voice</li>
        </ul>
        """
        
    def get_chinese_info(self):
        """Return Chinese info text"""
        return """
        <h3>🧑‍💻 开发者信息：</h3>
        <ul>
        <li><b>EmuFlash 开发者</b>: Dwi Bakti N Dev</li>
        <li><b>EmuFlash 管理器</b>: 版本 10.0.0</li>
        <li><b>功能</b>: 多语言支持，语音合成，游戏管理</li>
        <li><b>文本转语音</b>: 温柔女声</li>
        </ul>
        """
        
    def tr(self, key, *args):
        """Translate text based on current language"""
        text = self.languages[self.current_language].get(key, key)
        if args:
            try:
                return text.format(*args)
            except:
                return text
        return text
        
    def change_language(self, language):
        """Change application language"""
        if language in self.languages:
            self.current_language = language
            self.update_ui_language()
            self.save_game_data()
            
    def update_ui_language(self):
        """Update all UI elements with current language"""
        # Update window title
        self.setWindowTitle(self.tr("app_title"))
        
        # Update header
        self.current_game_title.setText(self.tr("select_game"))
        
        # Update button texts
        if hasattr(self, 'btn_upload'):
            self.btn_upload.setText(self.tr("upload_button"))
        if hasattr(self, 'btn_extract'):
            self.btn_extract.setText(self.tr("extract_button"))
        if hasattr(self, 'btn_rename'):
            self.btn_rename.setText(self.tr("rename_button"))
        if hasattr(self, 'btn_delete'):
            self.btn_delete.setText(self.tr("delete_button"))
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setText(self.tr("refresh_button"))
        
        # Update search placeholder
        if hasattr(self, 'search_box'):
            self.search_box.setPlaceholderText(self.tr("search_placeholder"))
        
        # Update combo box
        if hasattr(self, 'category_combo'):
            current_index = self.category_combo.currentIndex()
            self.category_combo.clear()
            self.category_combo.addItems(self.tr("filter_categories"))
            self.category_combo.setCurrentIndex(min(current_index, self.category_combo.count()-1))
        
        # Update tab texts
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setTabText(0, self.tr("player_tab"))
            self.tab_widget.setTabText(1, self.tr("manual_tab"))
            self.tab_widget.setTabText(2, self.tr("stats_tab"))
            self.tab_widget.setTabText(3, self.tr("info_tab"))
        
        # Update control buttons
        if hasattr(self, 'btn_play'):
            self.btn_play.setText(self.tr("play_button"))
        if hasattr(self, 'btn_stop'):
            self.btn_stop.setText(self.tr("stop_button"))
        if hasattr(self, 'btn_fullscreen'):
            self.btn_fullscreen.setText(self.tr("fullscreen_button"))
        
        # Update details buttons
        if hasattr(self, 'btn_edit_info'):
            self.btn_edit_info.setText(self.tr("edit_info"))
        if hasattr(self, 'btn_set_category'):
            self.btn_set_category.setText(self.tr("set_category"))
        if hasattr(self, 'btn_set_rating'):
            self.btn_set_rating.setText(self.tr("set_rating"))
        if hasattr(self, 'btn_take_screenshot'):
            self.btn_take_screenshot.setText(self.tr("take_screenshot"))
        if hasattr(self, 'btn_edit_cover'):
            self.btn_edit_cover.setText(self.tr("edit_cover"))
        
        # Update manual and info tabs
        if hasattr(self, 'tab_widget'):
            manual_widget = self.tab_widget.widget(1)
            if manual_widget:
                text_browser = manual_widget.findChild(QTextBrowser)
                if text_browser:
                    text_browser.setHtml(self.tr("manual_text"))
                    
            info_widget = self.tab_widget.widget(3)
            if info_widget:
                text_browser = info_widget.findChild(QTextBrowser)
                if text_browser:
                    text_browser.setHtml(self.tr("info_text"))
        
        # Update tray menu
        self.update_tray_menu_text()
        
    def update_tray_menu_text(self):
        """Update tray menu text"""
        if self.tray_icon:
            menu = self.tray_icon.contextMenu()
            if menu:
                actions = menu.actions()
                for action in actions:
                    if action.text() in ["Show/Hide", "显示/隐藏"]:
                        action.setText(self.tr("tray_show_hide"))
                    elif action.text() in ["Play Last Game", "播放最后游戏"]:
                        action.setText(self.tr("tray_play_last"))
                    elif action.text() in ["Recent Games", "最近游戏"]:
                        action.setText(self.tr("tray_recent_games"))
                    elif action.text() in ["Exit", "退出"]:
                        action.setText(self.tr("tray_exit"))
                    elif action.text() in ["🌐 Language", "🌐 语言"]:
                        action.setText(self.tr("language_menu"))
                    elif action.text() in ["🔊 TTS: ON", "🔊 TTS: OFF", "🔊 语音: 开", "🔊 语音: 关"]:
                        action.setText(self.tr("tts_toggle").replace("ON", "ON" if self.tts_enabled else "OFF").replace("开", "开" if self.tts_enabled else "关"))
                        
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("icon/icon.ico"))
            
            # Create tray menu
            tray_menu = QMenu()
            
            # Recent games menu with scrolling capability
            self.recent_games_menu = QMenu(self.tr("tray_recent_games"), self)
            tray_menu.addMenu(self.recent_games_menu)
            
            tray_menu.addSeparator()
            
            # Show/Hide action
            show_action = QAction(self.tr("tray_show_hide"), self)
            show_action.triggered.connect(self.toggle_visibility)
            tray_menu.addAction(show_action)
            
            # Play last game action
            play_last_action = QAction(self.tr("tray_play_last"), self)
            play_last_action.triggered.connect(self.play_last_game)
            tray_menu.addAction(play_last_action)
            
            tray_menu.addSeparator()
            
            # Website menu - 添加网站菜单
            website_menu = QMenu(self.tr("website_menu"), self)
            
            # 官方网站
            official_website_action = QAction(self.tr("Website Official 📝"), self)
            official_website_action.triggered.connect(lambda: self.open_website("https://royhtml.github.io/EmuFlash-V10/"))
            website_menu.addAction(official_website_action)
            
            # 帮助文档
            help_docs_action = QAction(self.tr("Download Games 📩"), self)
            help_docs_action.triggered.connect(lambda: self.open_website("https://mega.nz/folder/T8Rw1aqQ#LibEwt9QdgNU1aBMV6XLxw"))
            website_menu.addAction(help_docs_action)
            
            # GitHub仓库
            github_action = QAction("GitHub Dokumentasi ⚙️", self)
            github_action.triggered.connect(lambda: self.open_website("https://github.com/Royhtml/EmuFlash-V10"))
            website_menu.addAction(github_action)
            
            # GitHub仓库
            sosial_action = QAction("Sosial Media Dev 📱", self)
            sosial_action.triggered.connect(lambda: self.open_website("https://www.facebook.com/Royhtml/"))
            website_menu.addAction(sosial_action)
            
            tray_menu.addMenu(website_menu)
            
            # Language menu
            language_menu = QMenu(self.tr("language_menu"), self)
            
            english_action = QAction("English", self)
            english_action.triggered.connect(lambda: self.change_language("english"))
            language_menu.addAction(english_action)
            
            chinese_action = QAction("中文 (Chinese)", self)
            chinese_action.triggered.connect(lambda: self.change_language("chinese"))
            language_menu.addAction(chinese_action)
            
            tray_menu.addMenu(language_menu)
            
            # TTS toggle button (single button)
            tts_status = "ON" if self.tts_enabled else "OFF"
            if self.current_language == "chinese":
                tts_status = "开" if self.tts_enabled else "关"
            
            self.tts_toggle_action = QAction(f"🔊 TTS: {tts_status}", self)
            self.tts_toggle_action.triggered.connect(self.toggle_tts)
            tray_menu.addAction(self.tts_toggle_action)
            
            # Test TTS button
            tts_test_action = QAction(self.tr("tts_test"), self)
            tts_test_action.triggered.connect(self.test_tts)
            tray_menu.addAction(tts_test_action)
            
            tray_menu.addSeparator()
            
            # Exit action
            quit_action = QAction(self.tr("tray_exit"), self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Connect double click event
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            # Create timer for tray menu update
            self.tray_update_timer = QTimer()
            self.tray_update_timer.timeout.connect(self.update_tray_menu)
            self.tray_update_timer.start(5000)  # Update every 5 seconds
            
            # Update recent games
            self.update_recent_games_menu()
        
    def open_website(self, url):
        """Open website in default browser"""
        import webbrowser
        webbrowser.open(url)
            
    def toggle_tts(self):
        """Toggle TTS on/off with single button"""
        self.tts_enabled = not self.tts_enabled
        
        # Update button text
        tts_status = "ON" if self.tts_enabled else "OFF"
        if self.current_language == "chinese":
            tts_status = "开" if self.tts_enabled else "关"
        
        self.tts_toggle_action.setText(f"🔊 TTS: {tts_status}")
        
        # Speak confirmation
        if self.tts_enabled:
            if self.current_language == "english":
                self.speak("Text to speech enabled")
            else:
                self.speak("语音已启用")
        else:
            if self.tts_engine:
                self.tts_engine.stop()
        
        # Save setting
        self.save_game_data()
        
    def test_tts(self):
        """Test TTS functionality"""
        if self.current_language == "english":
            test_text = "Hello, this is a test of the text to speech system. EmuFlash Manager is working correctly."
        else:
            test_text = "你好，这是文本转语音系统的测试。EmuFlash 管理器工作正常。"
        self.speak(test_text)
        
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.play_last_game()
            
    def toggle_visibility(self):
        """Toggle show/hide window"""
        if self.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                self.tr("tray_notification"),
                self.tr("tray_app_running"),
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()
            
    def play_last_game(self):
        """Play the last opened game"""
        if self.current_game:
            self.play_game()
        else:
            # Find most recent game
            most_recent = None
            most_recent_time = None
            
            for game_name, game_info in self.game_data.items():
                if isinstance(game_info, dict) and 'last_played' in game_info:
                    try:
                        last_played = game_info['last_played']
                        if last_played:
                            last_time = datetime.strptime(last_played, "%Y-%m-%d %H:%M:%S")
                            if most_recent_time is None or last_time > most_recent_time:
                                most_recent_time = last_time
                                most_recent = game_name
                    except:
                        pass
            
            if most_recent:
                self.current_game = most_recent
                self.play_game()
            else:
                self.tray_icon.showMessage(
                    self.tr("tray_notification"),
                    "No games have been played yet" if self.current_language == "english" else "还没有玩过任何游戏",
                    QSystemTrayIcon.Warning,
                    2000
                )
                
    def update_recent_games_menu(self):
        """Update recent games menu in tray - FIXED: Show all available games"""
        if hasattr(self, 'recent_games_menu'):
            self.recent_games_menu.clear()
            
            # Collect ALL games from games directory
            all_games = []
            for file in os.listdir(self.games_dir):
                if file.lower().endswith(('.swf', '.zip')) and not file.startswith('.'):
                    # Get game info
                    game_info = self.game_data.get(file, {})
                    last_played = game_info.get('last_played', '')
                    
                    # Format display name (remove file extension for display)
                    display_name = os.path.splitext(file)[0]
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    all_games.append((file, display_name, last_played))
            
            # Sort by last played time (most recent first) and then alphabetically
            def sort_key(item):
                game_name, display_name, last_played = item
                if last_played:
                    try:
                        return (datetime.strptime(last_played, "%Y-%m-%d %H:%M:%S"), game_name)
                    except:
                        return (datetime.min, game_name)
                return (datetime.min, game_name)
            
            all_games.sort(key=sort_key, reverse=True)
            
            if all_games:
                # Create a scrollable area for games
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout(scroll_widget)
                scroll_layout.setContentsMargins(0, 0, 0, 0)
                
                # Create a scroll area
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                scroll_area.setFixedHeight(300)  # Fixed height for scrolling
                scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: 1px solid #555;
                        border-radius: 3px;
                        background-color: #2b2b2b;
                    }
                    QScrollBar:vertical {
                        background-color: #2b2b2b;
                        width: 12px;
                        border-radius: 6px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #4CAF50;
                        border-radius: 6px;
                        min-height: 20px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #66BB6A;
                    }
                """)
                
                # Create container for game buttons
                games_container = QWidget()
                games_container_layout = QVBoxLayout(games_container)
                games_container_layout.setSpacing(2)
                games_container_layout.setContentsMargins(5, 5, 5, 5)
                
                for game_file, display_name, last_played in all_games:
                    # Create clickable button for each game
                    game_btn = QPushButton(f"🎮 {display_name}")
                    game_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3a3a3a;
                            color: white;
                            border: 1px solid #555;
                            border-radius: 3px;
                            padding: 8px;
                            text-align: left;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #4CAF50;
                            border-color: #4CAF50;
                        }
                        QPushButton:pressed {
                            background-color: #2a2a2a;
                        }
                    """)
                    game_btn.setCursor(Qt.PointingHandCursor)
                    
                    # Connect click event
                    game_btn.clicked.connect(lambda checked, gn=game_file: self.play_game_from_tray(gn))
                    
                    # Add tooltip with last played time
                    if last_played:
                        game_btn.setToolTip(f"Last played: {last_played}")
                    else:
                        game_btn.setToolTip("Never played")
                    
                    games_container_layout.addWidget(game_btn)
                
                games_container_layout.addStretch()
                
                # Set games container as scroll area widget
                scroll_area.setWidget(games_container)
                scroll_layout.addWidget(scroll_area)
                
                # Add scroll widget to menu using QWidgetAction
                widget_action = QWidgetAction(self.recent_games_menu)
                widget_action.setDefaultWidget(scroll_widget)
                self.recent_games_menu.addAction(widget_action)
            else:
                no_game_text = "No games found" if self.current_language == "english" else "未找到游戏"
                no_game_action = QAction(no_game_text, self)
                no_game_action.setEnabled(False)
                self.recent_games_menu.addAction(no_game_action)
                
    def play_game_from_tray(self, game_name):
        """Play game directly from tray"""
        if not self.isVisible():
            self.show()
            
        self.current_game = game_name
        self.play_game()
        
    def update_tray_menu(self):
        """Periodically update tray menu"""
        self.update_recent_games_menu()
        
    def quit_application(self):
        """Exit application"""
        if self.emulator_process:
            self.stop_game()
        
        self.save_game_data()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        if self.tts_engine:
            self.tts_engine.stop()
            self.tts_engine = None
        
        QApplication.quit()
        
    def setup_ui(self):
        """Create professional and space-efficient UI"""
        self.setWindowTitle(self.tr("app_title"))
        
        # Set minimum and maximum size for responsiveness
        self.setMinimumSize(900, 600)
        
        # Central widget with vertical layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 1. Header with title and main buttons
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # 2. Main splitter for games panel and player
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Games list with covers
        left_panel = self.create_games_panel()
        self.main_splitter.addWidget(left_panel)
        
        # Right panel: Player and game info
        right_panel = self.create_player_panel()
        self.main_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([350, 650])
        
        # Make splitter adjustable by user
        self.main_splitter.setHandleWidth(10)
        
        main_layout.addWidget(self.main_splitter)
        
        # 3. Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.tr("status_ready", 0))
        
        # Style sheet for professional look
        self.setStyleSheet(self.get_stylesheet())
        
        # Set initial size based on screen resolution
        screen = QApplication.primaryScreen().geometry()
        if screen.height() <= 768:  # Small laptop
            self.resize(1000, 650)
        else:  # Large screen
            self.resize(1200, 800)
            
    def create_header(self):
        """Create header with title and main buttons"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Application title
        title_label = QLabel("🎮 EMUFLASH MANAGER")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #4CAF50;
            padding: 5px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Container for buttons with responsive layout
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Main action buttons
        btn_style = """
            QPushButton {
                padding: 6px 12px; 
                font-weight: bold;
                border-radius: 5px;
                min-width: 80px;
                font-size: 11px;
            }
        """
        
        # Create buttons and store references
        self.btn_upload = QPushButton(self.tr("upload_button"))
        self.btn_upload.setStyleSheet(btn_style + "background-color: #4CAF50;")
        self.btn_upload.clicked.connect(self.upload_game)
        self.btn_upload.setToolTip("Upload SWF or ZIP game")
        buttons_layout.addWidget(self.btn_upload)
        
        self.btn_extract = QPushButton(self.tr("extract_button"))
        self.btn_extract.setStyleSheet(btn_style + "background-color: #9C27B0;")
        self.btn_extract.clicked.connect(self.extract_zip)
        self.btn_extract.setToolTip("Extract ZIP file to game folder")
        buttons_layout.addWidget(self.btn_extract)
        
        self.btn_rename = QPushButton(self.tr("rename_button"))
        self.btn_rename.setStyleSheet(btn_style + "background-color: #2196F3;")
        self.btn_rename.clicked.connect(self.rename_game)
        self.btn_rename.setToolTip("Rename game")
        buttons_layout.addWidget(self.btn_rename)
        
        self.btn_delete = QPushButton(self.tr("delete_button"))
        self.btn_delete.setStyleSheet(btn_style + "background-color: #f44336;")
        self.btn_delete.clicked.connect(self.delete_game)
        self.btn_delete.setToolTip("Delete selected game")
        buttons_layout.addWidget(self.btn_delete)
        
        self.btn_refresh = QPushButton(self.tr("refresh_button"))
        self.btn_refresh.setStyleSheet(btn_style + "background-color: #FF9800;")
        self.btn_refresh.clicked.connect(self.load_games)
        self.btn_refresh.setToolTip("Refresh games list")
        buttons_layout.addWidget(self.btn_refresh)
        
        header_layout.addWidget(buttons_container)
        
        return header
        
    def create_games_panel(self):
        """Create games list panel with covers"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        
        # Search and filter controls
        filter_widget = self.create_filter_widget()
        layout.addWidget(filter_widget)
        
        # Splitter for games list and cover
        list_splitter = QSplitter(Qt.Vertical)
        
        # Top part: Games list with scrolling games
        list_widget = self.create_games_list_widget()
        list_splitter.addWidget(list_widget)
        
        # Bottom part: Cover preview
        cover_widget = self.create_cover_widget()
        list_splitter.addWidget(cover_widget)
        
        # Set splitter sizes
        list_splitter.setSizes([300, 200])
        list_splitter.setHandleWidth(5)
        
        layout.addWidget(list_splitter)
        
        return panel
        
    def create_filter_widget(self):
        """Create filter and search widget"""
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 5)
        filter_layout.setSpacing(5)
        
        # Search
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("🔍")
        search_label.setFixedWidth(20)
        search_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self.tr("search_placeholder"))
        self.search_box.textChanged.connect(self.filter_games)
        search_layout.addWidget(self.search_box)
        
        filter_layout.addWidget(search_widget)
        
        # Category filter
        category_widget = QWidget()
        category_layout = QHBoxLayout(category_widget)
        category_layout.setContentsMargins(0, 0, 0, 0)
        
        category_label = QLabel("📂")
        category_label.setFixedWidth(20)
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.tr("filter_categories"))
        self.category_combo.currentTextChanged.connect(self.filter_by_category)
        category_layout.addWidget(self.category_combo)
        
        filter_layout.addWidget(category_widget)
        
        return filter_widget
        
    def create_games_list_widget(self):
        """Create games list widget with scrolling games"""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel(self.tr("games_list"))
        list_label.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 2px;")
        list_layout.addWidget(list_label)
        
        # Scroll area for games with small covers - FIXED BACKGROUND AND TEXT COLOR
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                background-color: #1a1a1a;  /* Changed to black background */
            }
            QScrollBar:vertical {
                background-color: #252525;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4CAF50;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #66BB6A;
            }
        """)
        
        # Container for game cards - FIXED BACKGROUND
        self.games_container = QWidget()
        self.games_container.setStyleSheet("background-color: #1a1a1a;")  # Black background
        self.games_container_layout = QFlowLayout()
        self.games_container_layout.setSpacing(10)
        self.games_container_layout.setContentsMargins(10, 10, 10, 10)
        self.games_container.setLayout(self.games_container_layout)
        
        self.scroll_area.setWidget(self.games_container)
        list_layout.addWidget(self.scroll_area)
        
        return list_widget
        
    def create_game_card(self, game_name):
        """Create card for game with small cover - FIXED TEXT COLOR"""
        card = QWidget()
        card.setFixedSize(150, 200)
        card.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
            QWidget:hover {
                border-color: #4CAF50;
                background-color: #3a3a3a;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Cover image
        cover_label = QLabel()
        cover_label.setAlignment(Qt.AlignCenter)
        cover_label.setFixedSize(140, 100)
        cover_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        
        # Load cover or default icon
        cover_path = self.get_cover_path(game_name)
        if os.path.exists(cover_path):
            pixmap = QPixmap(cover_path)
            scaled_pixmap = pixmap.scaled(140, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cover_label.setPixmap(scaled_pixmap)
        else:
            # Set default icon
            if game_name.lower().endswith('.swf'):
                cover_label.setText("🎮")
                cover_label.setStyleSheet("""
                    QLabel {
                        font-size: 36px;
                        background-color: #1a1a1a;
                        border: 1px solid #555;
                        border-radius: 4px;
                    }
                """)
            else:
                cover_label.setText("📦")
                cover_label.setStyleSheet("""
                    QLabel {
                        font-size: 36px;
                        background-color: #1a1a1a;
                        border: 1px solid #555;
                        border-radius: 4px;
                    }
                """)
        
        layout.addWidget(cover_label)
        
        # Game name - FIXED: WHITE TEXT COLOR
        display_name = game_name[:20] + "..." if len(game_name) > 20 else game_name
        name_label = QLabel(display_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: white;  /* Changed to white */
                font-weight: bold;
                font-size: 10px;
            }
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Rating - FIXED: WHITE BACKGROUND FOR TEXT
        rating = "0"
        if game_name in self.game_data:
            rating = self.game_data[game_name].get('rating', '0')
        
        rating_label = QLabel("⭐" * int(rating) if rating.isdigit() else "⭐0")
        rating_label.setAlignment(Qt.AlignCenter)
        rating_label.setStyleSheet("color: #FFD700; font-size: 12px; background-color: transparent;")
        layout.addWidget(rating_label)
        
        # Play count - FIXED: WHITE BACKGROUND FOR TEXT
        play_count = 0
        if game_name in self.game_data:
            play_count = self.game_data[game_name].get('play_count', 0)
        
        count_label = QLabel(f"🎯 {play_count}")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("color: #4CAF50; font-size: 10px; background-color: transparent;")
        layout.addWidget(count_label)
        
        # Set mouse event for double click play
        card.mouseDoubleClickEvent = lambda e: self.play_game_direct(game_name)
        
        # Set context menu for card
        card.setContextMenuPolicy(Qt.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos, gn=game_name: self.show_card_context_menu(pos, gn))
        
        # Store game name as property
        card.game_name = game_name
        
        return card
        
    def show_card_context_menu(self, pos, game_name):
        """Show context menu for game card"""
        menu = QMenu(self)
        
        # Play action
        play_action = QAction("▶️ Play", self)
        play_action.triggered.connect(lambda: self.play_game_direct(game_name))
        menu.addAction(play_action)
        
        # Select action
        select_action = QAction("📌 Select", self)
        select_action.triggered.connect(lambda: self.select_game_by_name(game_name))
        menu.addAction(select_action)
        
        menu.addSeparator()
        
        # Edit action
        edit_action = QAction("✏️ Edit Info", self)
        edit_action.triggered.connect(lambda: self.edit_game_info_for(game_name))
        menu.addAction(edit_action)
        
        # Delete action
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.delete_game_by_name(game_name))
        menu.addAction(delete_action)
        
        menu.exec_(QCursor.pos())
        
    def select_game_by_name(self, game_name):
        """Select game by name"""
        self.current_game = game_name
        self.update_game_selection(game_name)
        
    def edit_game_info_for(self, game_name):
        """Edit info for specific game"""
        self.current_game = game_name
        self.edit_game_info()
        
    def delete_game_by_name(self, game_name):
        """Delete game by name"""
        self.current_game = game_name
        self.delete_game()
        
    def play_game_direct(self, game_name):
        """Play game directly from card"""
        self.current_game = game_name
        self.update_game_selection(game_name)
        self.play_game()
        # Speak game name using new function
        self.speak_game_start(game_name)
        
    def update_game_selection(self, game_name):
        """Update UI for selected game"""
        # Update current game title
        self.current_game_title.setText(f"🎮 {game_name}")
        
        # Update cover preview
        self.update_cover_preview(game_name)
        
        # Update game details
        self.select_game_direct(game_name)
        
        # Enable play button
        self.btn_play.setEnabled(True)
        self.btn_edit_cover.setEnabled(True)
        
    def select_game_direct(self, game_name):
        """Select game directly without list item"""
        game_path = os.path.join(self.games_dir, game_name)
        
        if os.path.exists(game_path):
            # Update info like in select_game
            size_bytes = os.path.getsize(game_path)
            size_str = self.format_size(size_bytes)
            
            mod_time = os.path.getmtime(game_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M")
            
            # Info from game data
            if game_name in self.game_data:
                game_info = self.game_data[game_name]
                category = game_info.get('category', 'Uncategorized')
                rating = game_info.get('rating', 'Not rated')
                play_count = game_info.get('play_count', 0)
                last_played = game_info.get('last_played', 'Never played')
                
                # Update game details
                details = f"<b>📊 Game Statistics:</b><br>"
                details += f"• Name: {game_name}<br>"
                details += f"• Category: {category}<br>"
                details += f"• Rating: {rating}/5<br>"
                details += f"• Played: {play_count} times<br>"
                details += f"• Last played: {last_played}<br>"
                details += f"• Size: {size_str}<br>"
                details += f"• Added: {mod_date}<br>"
                details += f"• EmuFlash Dev: Dwi Bakti N Dev<br>"
                
                description = game_info.get('description', '')
                if description:
                    details += f"<br><b>📝 Description:</b><br>{description}<br>"
                    
                controls = game_info.get('controls', '')
                if controls:
                    details += f"<br><b>🎮 Controls:</b><br>{controls}"
                    
                self.game_details.setHtml(details)
            else:
                self.game_details.setText(f"Game: {game_name}\nSize: {size_str}\nAdded: {mod_date}\n\nNo additional info available.")
            
            # Update player status
            self.player_status.setText(f"Status: Game '{game_name}' ready to play")
            self.player_status.setStyleSheet("color: #4CAF50; padding: 5px;")
            
            # Display preview in web view
            self.display_game_preview(game_name)
        
    def create_cover_widget(self):
        """Create widget for cover preview"""
        cover_widget = QGroupBox(self.tr("cover_preview"))
        cover_widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 15px;
            }
        """)
        cover_layout = QVBoxLayout()
        
        # Widget for cover preview
        self.cover_preview = QLabel()
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.cover_preview.setMinimumHeight(150)
        
        cover_layout.addWidget(self.cover_preview)
        
        # Edit cover button
        self.btn_edit_cover = QPushButton(self.tr("edit_cover"))
        self.btn_edit_cover.setStyleSheet("""
            QPushButton {
                padding: 5px;
                background-color: #FF9800;
                font-weight: bold;
            }
        """)
        self.btn_edit_cover.clicked.connect(self.edit_cover)
        self.btn_edit_cover.setEnabled(False)
        cover_layout.addWidget(self.btn_edit_cover)
        
        cover_widget.setLayout(cover_layout)
        return cover_widget
        
    def create_player_panel(self):
        """Create player panel and game controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(5)
        
        # Row 1: Game title
        self.current_game_title = QLabel(self.tr("select_game"))
        self.current_game_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #4CAF50;
            padding: 3px;
        """)
        layout.addWidget(self.current_game_title)
        
        # Row 2: Tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Player
        self.player_tab = self.create_player_tab()
        self.tab_widget.addTab(self.player_tab, self.tr("player_tab"))
        
        # Tab 2: Manual
        manual_tab = self.create_manual_tab()
        self.tab_widget.addTab(manual_tab, self.tr("manual_tab"))
        
        # Tab 3: Statistics
        stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(stats_tab, self.tr("stats_tab"))
        
        info_tab = self.create_info_tab()
        self.tab_widget.addTab(info_tab, self.tr("info_tab"))
        
        layout.addWidget(self.tab_widget)
        
        # Row 3: Game controls
        controls_group = self.create_controls_group()
        layout.addWidget(controls_group)
        
        # Row 4: Game info
        details_group = self.create_details_group()
        layout.addWidget(details_group)
        
        return panel
        
    def create_player_tab(self):
        """Create player tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Web view for preview
        self.web_view = QTextBrowser()
        self.web_view.setStyleSheet("""
            QTextBrowser {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
        """)
        self.web_view.setOpenExternalLinks(True)
        layout.addWidget(self.web_view)
        
        # Player status
        self.player_status = QLabel("Status: No game running")
        self.player_status.setStyleSheet("color: #FF9800; padding: 3px;")
        self.player_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.player_status)
        
        return tab
        
    def create_manual_tab(self):
        """Create manual tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        manual_browser = QTextBrowser()
        manual_browser.setHtml(self.tr("manual_text"))
        manual_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(manual_browser)
        
        return tab
    
    def create_info_tab(self):
        """Create info tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        info_browser = QTextBrowser()
        info_browser.setHtml(self.tr("info_text"))
        info_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(info_browser)
        
        return tab
        
    def create_stats_tab(self):
        """Create statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.stats_text = QTextBrowser()
        self.stats_text.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.stats_text)
        
        return tab
        
    def create_controls_group(self):
        """Create game controls group"""
        group = QGroupBox(self.tr("game_controls"))
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 15px;
            }
        """)
        layout = QHBoxLayout()
        
        # Main control buttons
        control_style = """
            QPushButton {
                padding: 8px 12px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 90px;
                font-size: 12px;
            }
        """
        
        self.btn_play = QPushButton(self.tr("play_button"))
        self.btn_play.setStyleSheet(control_style + "background-color: #4CAF50;")
        self.btn_play.clicked.connect(self.play_game)
        self.btn_play.setEnabled(False)
        layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton(self.tr("stop_button"))
        self.btn_stop.setStyleSheet(control_style + "background-color: #f44336;")
        self.btn_stop.clicked.connect(self.stop_game)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)
        
        self.btn_fullscreen = QPushButton(self.tr("fullscreen_button"))
        self.btn_fullscreen.setStyleSheet(control_style + "background-color: #2196F3;")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self.btn_fullscreen)
        
        layout.addStretch()
        
        # Volume control
        volume_widget = QWidget()
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        
        volume_label = QLabel("🔊")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("80%")
        self.volume_label.setFixedWidth(30)
        volume_layout.addWidget(self.volume_label)
        
        layout.addWidget(volume_widget)
        
        group.setLayout(layout)
        return group
        
    def create_details_group(self):
        """Create game details group"""
        group = QGroupBox(self.tr("game_details"))
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 15px;
            }
        """)
        layout = QVBoxLayout()
        
        self.game_details = QTextEdit()
        self.game_details.setReadOnly(True)
        self.game_details.setMaximumHeight(100)
        self.game_details.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.game_details)
        
        # Edit buttons
        edit_widget = QWidget()
        edit_layout = QHBoxLayout(edit_widget)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_edit_info = QPushButton(self.tr("edit_info"))
        self.btn_edit_info.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_edit_info.clicked.connect(self.edit_game_info)
        edit_layout.addWidget(self.btn_edit_info)
        
        self.btn_set_category = QPushButton(self.tr("set_category"))
        self.btn_set_category.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_set_category.clicked.connect(self.set_game_category)
        edit_layout.addWidget(self.btn_set_category)
        
        self.btn_set_rating = QPushButton(self.tr("set_rating"))
        self.btn_set_rating.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_set_rating.clicked.connect(self.set_game_rating)
        edit_layout.addWidget(self.btn_set_rating)
        
        self.btn_edit_cover = QPushButton(self.tr("edit_cover"))
        self.btn_edit_cover.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_edit_cover.clicked.connect(self.edit_cover)
        edit_layout.addWidget(self.btn_edit_cover)
        
        self.btn_take_screenshot = QPushButton(self.tr("take_screenshot"))
        self.btn_take_screenshot.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.btn_take_screenshot.clicked.connect(self.take_screenshot)
        edit_layout.addWidget(self.btn_take_screenshot)
        
        edit_layout.addStretch()
        layout.addWidget(edit_widget)
        
        group.setLayout(layout)
        return group
        
    def get_stylesheet(self):
        """Return stylesheet for application"""
        return """
            QMainWindow {
                background-color: black;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                color: black;  /* Changed default text color to white */
            }
            
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
            }
            QLineEdit, QTextEdit, QTextBrowser {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #4CAF50;
                font-size: 11px;
            }
            QComboBox {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
                min-width: 120px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: #ffffff;
                selection-background-color: #4CAF50;
                border: 1px solid #3a3a3a;
            }
            QLabel {
                color: black;  /* Changed to white */
                font-size: 11px;
            }
            QGroupBox {
                color: #4CAF50;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 12px;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #1e1e1e;
            }
            QStatusBar {
                background-color: #252525;
                color: #ffffff;
                border-top: 1px solid #3a3a3a;
                font-size: 11px;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: #ffffff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QSlider::groove:horizontal {
                background-color: #3a3a3a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #4CAF50;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #66BB6A;
            }
            QSplitter::handle {
                background-color: #3a3a3a;
            }
            QSplitter::handle:hover {
                background-color: #4CAF50;
            }
        """
        
    def load_game_data(self):
        """Load game data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Set current language if saved
                    if "system" in data and "language" in data["system"]:
                        self.current_language = data["system"]["language"]
                    return data
            except:
                return {}
        
        # Create default data template
        default_data = {
            "system": {
                "last_opened": "",
                "total_games": 0,
                "favorite_emulator": "FlashPlayeremuflash.exe",
                "start_minimized": False,
                "language": "english",
                "tts_enabled": True
            }
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
            
        return default_data
        
    def save_game_data(self):
        """Save game data to JSON file"""
        # Save language preference
        if "system" not in self.game_data:
            self.game_data["system"] = {}
        self.game_data["system"]["language"] = self.current_language
        self.game_data["system"]["tts_enabled"] = self.tts_enabled
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.game_data, f, indent=4, ensure_ascii=False)
            
    def ensure_games_dir(self):
        """Ensure games directory exists"""
        if not os.path.exists(self.games_dir):
            os.makedirs(self.games_dir)
            
        # Create subdirectories for screenshots and covers
        screenshots_dir = os.path.join(self.games_dir, "screenshots")
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
            
        covers_dir = os.path.join(self.games_dir, "covers")
        if not os.path.exists(covers_dir):
            os.makedirs(covers_dir)
            
    def load_games(self):
        """Load games list from directory into card view"""
        self.ensure_games_dir()
        
        # Clear existing cards
        for i in reversed(range(self.games_container_layout.count())): 
            widget = self.games_container_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Get all SWF and ZIP files from games folder
        game_files = []
        for file in os.listdir(self.games_dir):
            if file.lower().endswith(('.swf', '.zip')) and not file.startswith('.'):
                game_files.append(file)
                
        # Add game card for each file
        for game_file in sorted(game_files):
            game_card = self.create_game_card(game_file)
            self.games_container_layout.addWidget(game_card)
            
        # Update status bar
        self.status_bar.showMessage(self.tr("status_ready", len(game_files)))
        
        # Update statistics
        self.update_statistics()
        
        # Update recent games in tray
        if hasattr(self, 'recent_games_menu'):
            self.update_recent_games_menu()
        
    def update_cover_preview(self, game_name):
        """Update preview cover for game"""
        cover_path = self.get_cover_path(game_name)
        
        if os.path.exists(cover_path):
            # Load cover image
            pixmap = QPixmap(cover_path)
            
            # Adjust size to container
            container_size = self.cover_preview.size()
            scaled_pixmap = pixmap.scaled(
                container_size.width() - 20,
                container_size.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.cover_preview.setPixmap(scaled_pixmap)
            self.cover_preview.setText("")
        else:
            self.cover_preview.setText("No cover available")
            self.cover_preview.setPixmap(QPixmap())
            
    def get_cover_path(self, game_name):
        """Get cover path for game"""
        game_base = os.path.splitext(game_name)[0]
        covers_dir = os.path.join(self.games_dir, "covers")
        
        # Find image file with matching name
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        for ext in extensions:
            cover_path = os.path.join(covers_dir, f"{game_base}{ext}")
            if os.path.exists(cover_path):
                return cover_path
                
        return os.path.join(covers_dir, f"{game_base}.png")
        
    def edit_cover(self):
        """Edit game cover"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
            
        # Open dialog to select image
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Cover Image", 
            "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*.*)"
        )
        
        if file_path:
            try:
                covers_dir = os.path.join(self.games_dir, "covers")
                game_base = os.path.splitext(self.current_game)[0]
                cover_path = os.path.join(covers_dir, f"{game_base}.png")
                
                # Load image with PIL for consistency
                img = Image.open(file_path)
                
                # Convert to PNG if needed
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Save as PNG
                img.save(cover_path, 'PNG')
                
                # Update preview
                self.update_cover_preview(self.current_game)
                
                # Reload games to update card
                self.load_games()
                
                self.status_bar.showMessage(f"✅ Cover '{self.current_game}' updated successfully!")
                QMessageBox.information(self, "Success", "Game cover updated successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update cover:\n{str(e)}")
                
    def format_size(self, size_bytes):
        """Format file size to readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def get_flash_player_path(self):
        """Find Flash Player Emulator path"""
        target_file = "FlashPlayeremuflash.exe"
        
        search_paths = [
            ".",  # Current application folder
            "flash_player",
            "flash_emulator",
            "emulator",
            os.path.join(os.getcwd(), "flash_player"),
            os.path.join(os.getcwd(), "emulator"),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower() == target_file.lower():
                            return os.path.join(root, file)
        
        for root, dirs, files in os.walk("."):
            for file in files:
                if "flash" in file.lower() and file.lower().endswith('.exe'):
                    return os.path.join(root, file)
        
        exe_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_files.append(os.path.join(root, file))
        
        if exe_files:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self, "Select Flash Player Emulator", 
                ".", "Executable Files (*.exe);;All Files (*.*)"
            )
            
            if file_path and os.path.exists(file_path):
                self.game_data["system"]["flash_player_path"] = file_path
                self.save_game_data()
                return file_path
        
        return None
    
    def play_game(self):
        """Play selected game with Flash Player Emulator"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
            
        game_path = os.path.join(self.games_dir, self.current_game)
        if not os.path.exists(game_path):
            QMessageBox.critical(self, "Error", f"Game file not found: {game_path}")
            return
        
        self.player_status.setText(self.tr("status_emulator_search"))
        self.player_status.setStyleSheet("color: #FF9800; padding: 5px;")
        
        if self.current_game in self.game_data:
            play_count = self.game_data[self.current_game].get('play_count', 0)
            self.game_data[self.current_game]['play_count'] = play_count + 1
            self.game_data[self.current_game]['last_played'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_game_data()
        
        try:
            flash_player = self.get_flash_player_path()
            
            if flash_player and os.path.exists(flash_player):
                if self.emulator_process:
                    try:
                        self.emulator_process.terminate()
                        self.emulator_process = None
                    except:
                        pass
                
                if platform.system() == "Windows":
                    self.emulator_process = subprocess.Popen([flash_player, game_path])
                elif platform.system() == "Darwin":
                    self.emulator_process = subprocess.Popen(["open", "-a", flash_player, game_path])
                else:
                    self.emulator_process = subprocess.Popen([flash_player, game_path])
                    
                self.player_status.setText(self.tr("status_game_running", os.path.basename(flash_player)))
                self.status_bar.showMessage(f"Game '{self.current_game}' is running")
                
                self.btn_play.setEnabled(False)
                self.btn_stop.setEnabled(True)
                self.btn_fullscreen.setEnabled(True)
                
                # Speak notification using new function
                self.speak_game_start(self.current_game)
                
                # Update tray notification
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        self.tr("tray_notification"),
                        self.tr("tray_playing", self.current_game),
                        QSystemTrayIcon.Information,
                        2000
                    )
                
                # Update recent games menu
                self.update_recent_games_menu()
                
            else:
                QMessageBox.critical(
                    self, "Flash Player Not Found",
                    "Flash Player Emulator not found!\n\n"
                    "Please download or place FlashPlayeremuflash.exe in:\n"
                    "• Application folder\n"
                    "• 'flash_player' subfolder\n"
                    "• 'emulator' subfolder\n\n"
                    "Or use another .exe file that can open SWF files."
                )
                self.player_status.setText(self.tr("status_emulator_not_found"))
                self.player_status.setStyleSheet("color: #f44336; padding: 5px;")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open game:\n{str(e)}")
            self.player_status.setText("Status: Failed to open game")
            self.player_status.setStyleSheet("color: #f44336; padding: 5px;")
    
    def stop_game(self):
        """Stop game"""
        if self.emulator_process:
            try:
                self.emulator_process.terminate()
                self.emulator_process = None
            except:
                pass
        
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_fullscreen.setEnabled(False)
        
        self.player_status.setText(self.tr("status_game_stopped"))
        self.player_status.setStyleSheet("color: #FF9800; padding: 5px;")
        self.status_bar.showMessage("Game stopped")
        
        if self.current_game:
            self.display_game_preview(self.current_game)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.btn_fullscreen.setText(self.tr("fullscreen_button"))
        else:
            self.showFullScreen()
            self.btn_fullscreen.setText("🔳 Windowed")
    
    def change_volume(self, value):
        """Change volume"""
        self.volume_label.setText(f"{value}%")
    
    def minimize_to_tray(self):
        """Minimize window to system tray"""
        self.hide()
        if self.tray_icon:
            self.tray_icon.showMessage(
                self.tr("tray_notification"),
                "Application running in background\nDouble click tray icon to restore",
                QSystemTrayIcon.Information,
                3000
            )
    
    def upload_game(self):
        """Upload new game"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "Select Flash Game Files", 
            "", "Flash Files (*.swf *.zip);;All Files (*.*)"
        )
        
        if file_paths:
            success_count = 0
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(self.games_dir, file_name)
                
                if os.path.exists(dest_path):
                    reply = QMessageBox.question(
                        self, "File Already Exists",
                        f"File '{file_name}' already exists. Overwrite?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.No:
                        continue
                
                try:
                    shutil.copy2(file_path, dest_path)
                    
                    if file_name not in self.game_data:
                        self.game_data[file_name] = {
                            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "category": "Uncategorized",
                            "rating": "0",
                            "play_count": 0,
                            "last_played": "",
                            "description": "Classic Flash game",
                            "controls": "Arrow keys, Spacebar"
                        }
                    
                    success_count += 1
                    
                except Exception as e:
                    QMessageBox.critical(self, "Upload Failed", f"Error: {str(e)}")
            
            if success_count > 0:
                self.status_bar.showMessage(self.tr("status_upload_success", success_count))
                self.save_game_data()
                self.load_games()
                
                # Speak confirmation
                if self.tts_enabled:
                    if self.current_language == "english":
                        self.speak(f"{success_count} games uploaded successfully")
                    else:
                        self.speak(f"{success_count} 个游戏上传成功")
                
    def extract_zip(self):
        """Extract ZIP file to game folder"""
        if not self.current_game or not self.current_game.lower().endswith('.zip'):
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first!")
            return
            
        zip_path = os.path.join(self.games_dir, self.current_game)
        
        try:
            extract_dir = os.path.splitext(zip_path)[0]
            if os.path.exists(extract_dir):
                reply = QMessageBox.question(
                    self, "Folder Already Exists",
                    f"Folder '{os.path.basename(extract_dir)}' already exists.\nOverwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            swf_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith('.swf'):
                        swf_files.append(os.path.relpath(os.path.join(root, file), extract_dir))
            
            if swf_files:
                QMessageBox.information(
                    self, "Extract Successful",
                    f"ZIP file extracted successfully!\n\n"
                    f"Found {len(swf_files)} SWF files:\n"
                    f"{chr(10).join(swf_files[:5])}"
                    f"{chr(10)+'...' if len(swf_files) > 5 else ''}"
                )
            else:
                QMessageBox.information(
                    self, "Extract Successful",
                    "ZIP file extracted successfully!\n\n"
                    "No SWF files found in archive."
                )
            
            self.status_bar.showMessage(f"✅ File '{self.current_game}' extracted successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Extract Failed", f"Error: {str(e)}")
    
    def take_screenshot(self):
        """Take game screenshot"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
        
        screenshots_dir = os.path.join(self.games_dir, "screenshots")
        screenshot_file = os.path.join(screenshots_dir, 
                                     f"{os.path.splitext(self.current_game)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        # Create screenshot placeholder
        pixmap = QPixmap(800, 600)
        pixmap.fill(QColor(30, 30, 30))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, f"{self.current_game}")
        
        painter.setFont(QFont("Arial", 16))
        painter.drawText(pixmap.rect(), Qt.AlignCenter | Qt.AlignBottom, 
                        f"Screenshot - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        painter.end()
        
        pixmap.save(screenshot_file, "PNG")
        
        self.status_bar.showMessage(f"📸 Screenshot saved: {os.path.basename(screenshot_file)}")
        QMessageBox.information(self, "Screenshot", 
                               f"Screenshot saved successfully:\n{screenshot_file}")
        
        # Speak confirmation
        if self.tts_enabled:
            if self.current_language == "english":
                self.speak("Screenshot taken")
            else:
                self.speak("截图已保存")
    
    def delete_game(self):
        """Delete selected game"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
            
        reply = QMessageBox.question(
            self, self.tr("confirm_delete"),
            self.tr("delete_message", self.current_game),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                game_path = os.path.join(self.games_dir, self.current_game)
                
                if self.emulator_process:
                    self.stop_game()
                
                os.remove(game_path)
                
                # Delete related screenshots
                screenshots_dir = os.path.join(self.games_dir, "screenshots")
                game_base = os.path.splitext(self.current_game)[0]
                for file in os.listdir(screenshots_dir):
                    if file.startswith(game_base):
                        os.remove(os.path.join(screenshots_dir, file))
                
                # Delete related cover
                cover_path = self.get_cover_path(self.current_game)
                if os.path.exists(cover_path):
                    os.remove(cover_path)
                
                if self.current_game in self.game_data:
                    del self.game_data[self.current_game]
                    self.save_game_data()
                
                self.status_bar.showMessage(f"🗑️ Game '{self.current_game}' deleted successfully!")
                self.current_game = None
                self.load_games()
                
                # Update recent games menu
                self.update_recent_games_menu()
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Error: {str(e)}")
    
    def rename_game(self):
        """Rename selected game"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
            
        new_name, ok = QInputDialog.getText(
            self, "Rename Game", 
            "Enter new name:", 
            QLineEdit.Normal, 
            self.current_game
        )
        
        if ok and new_name and new_name != self.current_game:
            old_ext = os.path.splitext(self.current_game)[1]
            if not new_name.endswith(old_ext):
                new_name += old_ext
                
            old_path = os.path.join(self.games_dir, self.current_game)
            new_path = os.path.join(self.games_dir, new_name)
            
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "File with that name already exists!")
                return
                
            try:
                os.rename(old_path, new_path)
                
                if self.current_game in self.game_data:
                    self.game_data[new_name] = self.game_data.pop(self.current_game)
                    self.save_game_data()
                
                # Rename screenshot
                screenshots_dir = os.path.join(self.games_dir, "screenshots")
                old_base = os.path.splitext(self.current_game)[0]
                new_base = os.path.splitext(new_name)[0]
                
                for file in os.listdir(screenshots_dir):
                    if file.startswith(old_base):
                        old_file = os.path.join(screenshots_dir, file)
                        new_file = os.path.join(screenshots_dir, file.replace(old_base, new_base, 1))
                        os.rename(old_file, new_file)
                
                # Rename cover
                old_cover_path = self.get_cover_path(self.current_game)
                if os.path.exists(old_cover_path):
                    new_cover_path = old_cover_path.replace(old_base, new_base)
                    os.rename(old_cover_path, new_cover_path)
                
                self.status_bar.showMessage(f"✏️ Game renamed to '{new_name}' successfully!")
                self.current_game = new_name
                self.load_games()
                
            except Exception as e:
                QMessageBox.critical(self, "Rename Failed", f"Error: {str(e)}")
    
    def edit_game_info(self):
        """Edit game information"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Info: {self.current_game}")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        category_combo = QComboBox()
        categories = ["Action", "Adventure", "Puzzle", "Arcade", "Strategy", "Sport", "Racing", 
                     "Educational", "Shooter", "Simulation", "Other", "Uncategorized"]
        category_combo.addItems(categories)
        
        if self.current_game in self.game_data:
            current_category = self.game_data[self.current_game].get('category', 'Uncategorized')
            index = category_combo.findText(current_category)
            if index >= 0:
                category_combo.setCurrentIndex(index)
        
        form_layout.addRow("Category:", category_combo)
        
        rating_slider = QSlider(Qt.Horizontal)
        rating_slider.setRange(0, 5)
        rating_slider.setTickPosition(QSlider.TicksBelow)
        rating_slider.setTickInterval(1)
        
        rating_label = QLabel("0")
        
        if self.current_game in self.game_data:
            current_rating = int(self.game_data[self.current_game].get('rating', 0))
            rating_slider.setValue(current_rating)
            rating_label.setText(str(current_rating))
        
        rating_slider.valueChanged.connect(lambda v: rating_label.setText(str(v)))
        
        rating_widget = QWidget()
        rating_layout = QHBoxLayout(rating_widget)
        rating_layout.addWidget(rating_slider)
        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(QLabel("/5"))
        
        form_layout.addRow("Rating:", rating_widget)
        
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(80)
        
        if self.current_game in self.game_data:
            description_edit.setText(self.game_data[self.current_game].get('description', ''))
        
        form_layout.addRow("Description:", description_edit)
        
        controls_edit = QLineEdit()
        
        if self.current_game in self.game_data:
            controls_edit.setText(self.game_data[self.current_game].get('controls', 'Arrow keys, Spacebar'))
        else:
            controls_edit.setText("Arrow keys, Spacebar")
        
        form_layout.addRow("Controls:", controls_edit)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Save")
        btn_save.clicked.connect(lambda: self.save_game_info(
            dialog, category_combo.currentText(), 
            rating_slider.value(), description_edit.toPlainText(),
            controls_edit.text()
        ))
        button_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def save_game_info(self, dialog, category, rating, description, controls):
        """Save game information"""
        if self.current_game not in self.game_data:
            self.game_data[self.current_game] = {}
        
        self.game_data[self.current_game]['category'] = category
        self.game_data[self.current_game]['rating'] = str(rating)
        self.game_data[self.current_game]['description'] = description
        self.game_data[self.current_game]['controls'] = controls
        
        self.save_game_data()
        self.select_game_direct(self.current_game)
        
        dialog.accept()
        self.status_bar.showMessage(f"✅ Game info '{self.current_game}' updated!")
        
    def set_game_category(self):
        """Set game category"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
        
        categories = ["Action", "Adventure", "Puzzle", "Arcade", "Strategy", "Sport", 
                     "Racing", "Educational", "Shooter", "Simulation", "Other"]
        
        category, ok = QInputDialog.getItem(
            self, "Set Category", "Select category:", 
            categories, 0, False
        )
        
        if ok and category:
            if self.current_game not in self.game_data:
                self.game_data[self.current_game] = {}
            
            self.game_data[self.current_game]['category'] = category
            self.save_game_data()
            
            self.select_game_direct(self.current_game)
            self.status_bar.showMessage(f"📂 Category '{self.current_game}' changed to '{category}'")
    
    def set_game_rating(self):
        """Set game rating"""
        if not self.current_game:
            QMessageBox.warning(self, "Warning", self.tr("warning_select_game"))
            return
        
        rating, ok = QInputDialog.getInt(
            self, "Set Rating", "Give rating (0-5):", 
            min=0, max=5, step=1
        )
        
        if ok:
            if self.current_game not in self.game_data:
                self.game_data[self.current_game] = {}
            
            self.game_data[self.current_game]['rating'] = str(rating)
            self.save_game_data()
            
            self.select_game_direct(self.current_game)
            self.status_bar.showMessage(f"⭐ Rating '{self.current_game}' changed to {rating}/5")
    
    def filter_games(self, text):
        """Filter games based on search text"""
        for i in range(self.games_container_layout.count()):
            widget = self.games_container_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'game_name'):
                game_name = widget.game_name
                widget.setVisible(text.lower() in game_name.lower())
    
    def filter_by_category(self, category):
        """Filter games by category"""
        if category == self.tr("filter_categories")[0]:  # "All" or "全部"
            for i in range(self.games_container_layout.count()):
                widget = self.games_container_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            return
        
        for i in range(self.games_container_layout.count()):
            widget = self.games_container_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'game_name'):
                game_name = widget.game_name
                
                if game_name in self.game_data:
                    game_category = self.game_data[game_name].get('category', 'Uncategorized')
                    widget.setVisible(game_category == category)
                else:
                    widget.setVisible(category == self.tr("filter_categories")[-1])  # "Uncategorized" or "未分类"
    
    def update_statistics(self):
        """Update game statistics"""
        total_games = self.games_container_layout.count()
        swf_count = 0
        zip_count = 0
        total_size = 0
        
        for i in range(total_games):
            widget = self.games_container_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'game_name'):
                game_name = widget.game_name
                game_path = os.path.join(self.games_dir, game_name)
                
                if os.path.exists(game_path):
                    total_size += os.path.getsize(game_path)
                    
                    if game_name.lower().endswith('.swf'):
                        swf_count += 1
                    elif game_name.lower().endswith('.zip'):
                        zip_count += 1
        
        stats_html = f"""
        <html>
        <body style="background-color: #252525; color: white; padding: 10px;">
            <h3 style="color: #4CAF50;">📊 Collection Statistics</h3>
            
            <div style="background-color: #2b2b2b; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                <p>• Total Games: <b>{total_games}</b></p>
                <p>• SWF Files: <b>{swf_count}</b></p>
                <p>• ZIP Archives: <b>{zip_count}</b></p>
                <p>• Total Size: <b>{self.format_size(total_size)}</b></p>
            </div>
        """
        
        popular_games = []
        for game_name in self.game_data:
            if isinstance(self.game_data[game_name], dict):
                play_count = self.game_data[game_name].get('play_count', 0)
                if play_count > 0:
                    popular_games.append((game_name, play_count))
        
        popular_games.sort(key=lambda x: x[1], reverse=True)
        
        stats_html += """
            <div style="background-color: #2b2b2b; padding: 10px; border-radius: 6px;">
                <h4>🎮 Most Popular Games</h4>
        """
        
        for game_name, play_count in popular_games[:5]:
            stats_html += f"<p>• {game_name}: <b>{play_count}</b> times</p>"
        
        if not popular_games:
            stats_html += "<p><i>No play data available</i></p>"
        
        stats_html += """
            </div>
            
            <div style="margin-top: 15px; padding: 8px; background-color: #1a1a1a; border-radius: 4px;">
                <p><i>Updated: """ + datetime.now().strftime("%d/%m/%Y %H:%M") + """</i></p>
            </div>
        </body>
        </html>
        """
        
        self.stats_text.setHtml(stats_html)
    
    def display_game_preview(self, game_name):
        """Display game preview in web view"""
        if game_name.lower().endswith('.swf'):
            preview_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        background-color: #1a1a1a;
                        color: white;
                        font-family: Arial, sans-serif;
                        padding: 15px;
                        font-size: 12px;
                    }}
                    .game-info {{
                        background-color: #252525;
                        padding: 10px;
                        border-radius: 8px;
                        margin-bottom: 15px;
                        border-left: 4px solid #4CAF50;
                    }}
                    .warning {{
                        background-color: #FF9800;
                        color: #000;
                        padding: 8px;
                        border-radius: 4px;
                        font-weight: bold;
                        margin-top: 15px;
                        font-size: 11px;
                    }}
                </style>
            </head>
            <body>
                <div class="game-info">
                    <h3>🎮 {game_name}</h3>
                    <p>Flash SWF file ready to play</p>
                    <p>Double click on game card to play immediately</p>
                </div>
                
                <div class="warning">
                    ⚠️ Make sure FlashPlayeremuflash.exe is available!
                </div>
            </body>
            </html>
            """
        else:
            preview_html = f"""
            <html>
            <body style="background-color: #1a1a1a; color: white; padding: 15px; font-size: 12px;">
                <h3 style="color: #FF9800;">📦 Archive File: {game_name}</h3>
                <p>ZIP file containing Flash games</p>
                <p>Click Extract button to extract contents</p>
                <p>After extraction, SWF files will appear in games list</p>
            </body>
            </html>
            """
            
        self.web_view.setHtml(preview_html)
        
    def resizeEvent(self, event):
        """Handle resize event for responsiveness"""
        super().resizeEvent(event)
        
        # Update cover preview when size changes
        if self.current_game:
            self.update_cover_preview(self.current_game)
        
        # Adjust splitter sizes based on window size
        window_width = self.width()
        if window_width < 1000:  # Small screen
            self.main_splitter.setSizes([250, 550])
        elif window_width < 1200:  # Medium screen
            self.main_splitter.setSizes([300, 650])
        else:  # Large screen
            self.main_splitter.setSizes([350, 750])
    
    def closeEvent(self, event):
        """Handle application closing - minimize to tray"""
        event.ignore()  # Ignore close event
        self.minimize_to_tray()  # Minimize to tray

# Custom Flow Layout
class QFlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itemList = []
        self.hSpacing = 6
        self.vSpacing = 6
        
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
            
    def addItem(self, item):
        self.itemList.append(item)
        
    def count(self):
        return len(self.itemList)
    
    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Horizontal | Qt.Vertical)
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
    
    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.hSpacing
            spaceY = self.vSpacing
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        return y + lineHeight - rect.y()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application info
    app.setApplicationName("EmuFlash Manager")
    app.setApplicationVersion("2.1")
    
    # Check games directory
    if not os.path.exists("flash_games"):
        os.makedirs("flash_games")
        print("Directory 'flash_games' created.")
    
    # Check Flash Player Emulator
    emulator_found = False
    search_locations = [".", "flash_player", "emulator"]
    
    print("\n🔍 Searching for Flash Player Emulator...")
    for location in search_locations:
        if os.path.exists(location):
            for root, dirs, files in os.walk(location):
                for file in files:
                    if file.lower() == "flashplayeremuflash.exe" or ("flash" in file.lower() and file.lower().endswith('.exe')):
                        emulator_found = True
                        print(f"✅ Emulator found: {os.path.join(root, file)}")
    
    if not emulator_found:
        print("\n⚠️  WARNING: Flash Player Emulator not found!")
        print("Please place FlashPlayeremuflash.exe in one of these locations:")
        print("1. Application folder (where .py file is located)")
        print("2. 'flash_player' subfolder")
        print("3. 'emulator' subfolder")
        print("\nOr use another .exe file that can open SWF files.")
        print("When running a game for the first time, you'll be asked to select emulator file.")
    
    # Create and show window
    window = FlashGameManager()
    window.show()
    
    # Check if should start minimized
    if "system" in window.game_data:
        if window.game_data["system"].get("start_minimized", False):
            window.showMinimized()
    
    # Load TTS settings
    if "system" in window.game_data:
        window.tts_enabled = window.game_data["system"].get("tts_enabled", True)
    
    sys.exit(app.exec_())

import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


def run_gui():
    # Set DPI Awareness (Windows only)
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            print(f"Warning: DPI awareness setting failed: {e}")

    app = QtWidgets.QApplication(sys.argv)
    window = FlashGameManager()
    window.show()

    sys.exit(app.exec_())


def run_cli():
    run_gui()


if __name__ == "__main__":
    run_gui()

