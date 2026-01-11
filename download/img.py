import sys
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QScrollArea, QComboBox, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPalette, QColor, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import urllib.parse

class ImageDownloadThread(QThread):
    """Thread untuk download gambar"""
    image_downloaded = pyqtSignal(QPixmap, int)
    
    def __init__(self, url, index):
        super().__init__()
        self.url = url
        self.index = index
        
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                image = QImage()
                image.loadFromData(response.content)
                pixmap = QPixmap.fromImage(image)
                self.image_downloaded.emit(pixmap, self.index)
        except Exception as e:
            print(f"Download error: {e}")

class GameImageSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_styles()
        self.setup_variables()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Game Image Search")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_frame = QFrame()
        header_frame.setMaximumHeight(80)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("🎮 Game Image Search")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #bb86fc;")
        
        header_layout.addWidget(title_label)
        main_layout.addWidget(header_frame)
        
        # Search controls
        controls_frame = QFrame()
        controls_frame.setMaximumHeight(60)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(15)
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇬🇧 English", "en")
        self.language_combo.addItem("🇨🇳 中文", "zh")
        self.language_combo.setFixedWidth(150)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for game images...")
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(self.search_images)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setMinimumWidth(100)
        self.search_btn.clicked.connect(self.search_images)
        
        controls_layout.addWidget(self.language_combo)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(self.search_btn)
        main_layout.addWidget(controls_frame)
        
        # Image display area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll)
        
        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        self.image_layout.setAlignment(Qt.AlignTop)
        self.image_layout.setSpacing(15)
        
        scroll_area.setWidget(self.image_container)
        main_layout.addWidget(scroll_area, 1)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cf6679; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
    def setup_styles(self):
        """Setup dark theme styles"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, QColor(200, 200, 200))
        dark_palette.setColor(QPalette.Base, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, QColor(200, 200, 200))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(187, 134, 252))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(dark_palette)
        
        style = """
        QMainWindow {
            background-color: #1e1e1e;
        }
        
        QFrame {
            background-color: #2d2d2d;
            border-radius: 10px;
            border: 1px solid #3d3d3d;
        }
        
        QLineEdit {
            background-color: #3d3d3d;
            border: 2px solid #4d4d4d;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
            color: white;
            selection-background-color: #bb86fc;
        }
        
        QLineEdit:focus {
            border: 2px solid #bb86fc;
        }
        
        QPushButton {
            background-color: #6200ee;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #7c4dff;
        }
        
        QPushButton:pressed {
            background-color: #3700b3;
        }
        
        QComboBox {
            background-color: #3d3d3d;
            border: 2px solid #4d4d4d;
            border-radius: 8px;
            padding: 8px;
            color: white;
            min-height: 20px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            selection-background-color: #6200ee;
            color: white;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #6200ee;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #7c4dff;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        """
        
        self.setStyleSheet(style)
        
    def setup_variables(self):
        """Setup variables and managers"""
        self.current_language = "en"
        self.current_page = 1
        self.is_loading = False
        self.has_more = True
        self.search_term = ""
        self.images_data = []
        self.download_threads = []
        
        # Network manager
        self.network_manager = QNetworkAccessManager()
        
        # Translations
        self.translations = {
            "en": {
                "search_placeholder": "Search for game images...",
                "search_btn": "Search",
                "loading": "Loading...",
                "no_results": "No results found",
                "error": "Error occurred",
                "load_more": "Loading more...",
                "search_prompt": "Enter game name to search",
                "connection_error": "Connection error",
                "no_games": "No game images found"
            },
            "zh": {
                "search_placeholder": "搜索游戏图片...",
                "search_btn": "搜索",
                "loading": "加载中...",
                "no_results": "未找到结果",
                "error": "发生错误",
                "load_more": "正在加载更多...",
                "search_prompt": "输入游戏名称进行搜索",
                "connection_error": "连接错误",
                "no_games": "未找到游戏图片"
            }
        }
        
    def change_language(self):
        """Change application language"""
        self.current_language = self.language_combo.currentData()
        self.update_ui_text()
        
    def update_ui_text(self):
        """Update UI text based on selected language"""
        trans = self.translations[self.current_language]
        self.search_input.setPlaceholderText(trans["search_placeholder"])
        self.search_btn.setText(trans["search_btn"])
        
    def search_images(self):
        """Search for game images"""
        query = self.search_input.text().strip()
        if not query:
            self.show_message("search_prompt")
            return
            
        self.search_term = f"{query} game video game gaming esports"  # Force game-related results
        self.current_page = 1
        self.images_data = []
        self.clear_images()
        self.load_images()
        
    def load_images(self):
        """Load images from Unsplash"""
        if self.is_loading or not self.has_more:
            return
            
        self.is_loading = True
        self.show_message("loading")
        
        # Unsplash API endpoint
        encoded_query = urllib.parse.quote(self.search_term)
        url = f"https://api.unsplash.com/search/photos?query={encoded_query}&page={self.current_page}&per_page=20&orientation=landscape"
        
        # API key - replace with your Unsplash API key
        headers = {
            "Authorization": "Client-ID bNf1fq2p6XENfQnZ6KAne40raJcwkzxFs4DWTvZHuY8"  # Replace with your actual API key
        }
        
        request = QNetworkRequest(url)
        for key, value in headers.items():
            request.setRawHeader(key.encode(), value.encode())
            
        self.network_manager.finished.connect(self.handle_response)
        self.network_manager.get(request)
        
    def handle_response(self, reply):
        """Handle API response"""
        self.network_manager.finished.disconnect(self.handle_response)
        
        try:
            if reply.error() == QNetworkReply.NoError:
                data = json.loads(reply.readAll().data().decode('utf-8'))
                results = data.get('results', [])
                
                if results:
                    self.images_data.extend(results)
                    self.display_images()
                    self.current_page += 1
                    self.has_more = len(results) == 20
                else:
                    if self.current_page == 1:
                        self.show_message("no_games")
                    self.has_more = False
            else:
                self.show_message("connection_error")
                
        except Exception as e:
            print(f"Error: {e}")
            self.show_message("error")
            
        finally:
            self.is_loading = False
            if not self.images_data and self.current_page == 1:
                self.show_message("no_results")
            else:
                self.status_label.setText("")
                
    def display_images(self):
        """Display images in grid"""
        trans = self.translations[self.current_language]
        
        # Create image rows
        for i in range(0, len(self.images_data), 4):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(15)
            
            for j in range(4):
                idx = i + j
                if idx >= len(self.images_data):
                    break
                    
                img_data = self.images_data[idx]
                
                # Image container
                img_container = QFrame()
                img_container.setFixedSize(280, 200)
                img_container.setStyleSheet("""
                    QFrame {
                        background-color: #3d3d3d;
                        border-radius: 8px;
                        border: 1px solid #4d4d4d;
                    }
                """)
                
                img_layout = QVBoxLayout(img_container)
                img_layout.setContentsMargins(5, 5, 5, 5)
                
                # Image label with loading animation
                img_label = QLabel()
                img_label.setFixedSize(270, 150)
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("""
                    QLabel {
                        background-color: #2d2d2d;
                        border-radius: 5px;
                    }
                """)
                
                # Loading animation
                loading_label = QLabel("🔄")
                loading_label.setAlignment(Qt.AlignCenter)
                img_layout.addWidget(loading_label)
                
                # Description
                desc_label = QLabel(img_data.get('alt_description', 'Game Image')[:30] + '...')
                desc_label.setAlignment(Qt.AlignCenter)
                desc_label.setStyleSheet("color: #bbbbbb; font-size: 12px; padding: 5px;")
                img_layout.addWidget(desc_label)
                
                row_layout.addWidget(img_container)
                
                # Start downloading image
                thread = ImageDownloadThread(img_data['urls']['small'], idx)
                thread.image_downloaded.connect(self.on_image_downloaded)
                thread.start()
                self.download_threads.append(thread)
                
            self.image_layout.addWidget(row_widget)
            
    def on_image_downloaded(self, pixmap, index):
        """Handle downloaded image"""
        # Find the corresponding label and update it
        row_index = index // 4
        col_index = index % 4
        
        if row_index < self.image_layout.count():
            row_widget = self.image_layout.itemAt(row_index).widget()
            if row_widget and col_index < row_widget.layout().count():
                img_container = row_widget.layout().itemAt(col_index).widget()
                if img_container:
                    # Clear loading label
                    for i in reversed(range(img_container.layout().count())):
                        widget = img_container.layout().itemAt(i).widget()
                        if isinstance(widget, QLabel) and widget.text() == "🔄":
                            img_container.layout().removeWidget(widget)
                            widget.deleteLater()
                            break
                    
                    # Add image
                    img_label = QLabel()
                    img_label.setFixedSize(270, 150)
                    scaled_pixmap = pixmap.scaled(270, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled_pixmap)
                    img_label.setAlignment(Qt.AlignCenter)
                    img_label.setStyleSheet("border-radius: 5px;")
                    
                    img_container.layout().insertWidget(0, img_label)
                    
                    # Fade-in animation
                    animation = QPropertyAnimation(img_label, b"windowOpacity")
                    animation.setDuration(300)
                    animation.setStartValue(0)
                    animation.setEndValue(1)
                    animation.setEasingCurve(QEasingCurve.InOutQuad)
                    animation.start()
        
    def check_scroll(self, value):
        """Check if scrolled to bottom for infinite scroll"""
        scrollbar = self.image_container.parent().verticalScrollBar()
        if value > scrollbar.maximum() * 0.8 and not self.is_loading and self.has_more:
            QTimer.singleShot(300, self.load_images)
            
    def clear_images(self):
        """Clear all displayed images"""
        # Clean up threads
        for thread in self.download_threads:
            if thread.isRunning():
                thread.terminate()
        self.download_threads = []
        
        # Clear layout
        while self.image_layout.count():
            item = self.image_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def show_message(self, message_key):
        """Show status message"""
        trans = self.translations[self.current_language]
        self.status_label.setText(trans[message_key])
        
    def closeEvent(self, event):
        """Clean up on close"""
        for thread in self.download_threads:
            if thread.isRunning():
                thread.terminate()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = GameImageSearchApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()