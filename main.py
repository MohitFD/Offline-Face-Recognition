

# import os
# import sys
# import cv2
# import datetime
# import importlib.metadata
# from PyQt5.QtWidgets import (
#     QApplication,
#     QWidget,
#     QLabel,
#     QPushButton,
#     QVBoxLayout,
#     QHBoxLayout,
#     QTableWidget,
#     QTableWidgetItem,
#     QHeaderView,
#     QFrame,
#     QLineEdit,
#     QDialog,
#     QDialogButtonBox,
#     QMessageBox,
#     QGridLayout,
#     QSpacerItem,
#     QSizePolicy,
#     QCalendarWidget,
#     QScrollArea,
#     QToolButton,
#     QStyle,
#     QStyledItemDelegate,
#     QTableView,
#     QGraphicsDropShadowEffect,
# )
# from PyQt5.QtCore import (
#     QTimer,
#     Qt,
#     pyqtSignal,
#     QThread,
#     QSize,
#     QDate,
#     QPropertyAnimation,
#     QEasingCurve,
#     QPoint,
# )
# from PyQt5.QtGui import (
#     QImage,
#     QPixmap,
#     QPainter,
#     QPainterPath,
#     QColor,
#     QFont,
#     QPen,
#     QBrush,
#     QIcon,
#     QRegion,
#     QCursor, 
#     QPalette
# )
# from fetch_emp_from_fixhr import fetch_and_store_employees
# from login import login_fixhr, is_logged_in, load_session, clear_session
# from database import (
#     get_attendance_logs,
#     get_daily_attendance_summary,
#     get_employee_count,
#     get_attendance_by_date,
#     init_db,
#     start_background_sync,
#     get_sync_status_overview,
# )
# from device_info import get_device_info, is_internet_available
# from speak import speak
# from backup_utils import BackupManager
# import io

# # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# if sys.stdout is not None:
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# else:
#     sys.stdout = io.TextIOWrapper(open(os.devnull, 'w').detach(), encoding="utf-8")

# def format_date_ddmmyy(date_str: str) -> str:
#     try:
#         dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
#         return dt.strftime("%d-%m-%y")
#     except Exception:
#         try:
#             dt = datetime.datetime.strptime(date_str, "%Y/%m/%d")
#             return dt.strftime("%d-%m-%y")
#         except Exception:
#             return date_str

# class FetchThread(QThread):
#     finished = pyqtSignal(bool, str)

#     def __init__(self, token):
#         super().__init__()
#         self.token = token

#     def run(self):
#         try:
#             fetch_and_store_employees(self.token)
#             self.finished.emit(True, "Employees fetched successfully")
#         except Exception as e:
#             self.finished.emit(False, str(e))

# class LivenessLoaderThread(QThread):
#     finished = pyqtSignal(bool, str, object)

#     def run(self):
#         try:
#             from liveness_detector import detect_and_predict
#             self.finished.emit(
#                 True, "Liveness detector loaded successfully", detect_and_predict
#             )
#         except ImportError as e:
#             self.finished.emit(False, f"Failed to load liveness detector: {e}", None)
#         except Exception as e:
#             self.finished.emit(False, f"Unexpected error loading detector: {e}", None)

# class DetectWorker(QThread):
#     result_ready = pyqtSignal(dict)

#     def __init__(self, detector_fn, frame):
#         super().__init__()
#         self.detector_fn = detector_fn
#         self.frame = frame

#     def run(self):
#         try:
#             result = self.detector_fn(self.frame)
#         except Exception as e:
#             result = {
#                 "status": False,
#                 "emp_full_name": "System Error",
#                 "message": str(e),
#             }
#         self.result_ready.emit(result)

# class ModernCard(QFrame):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet(
#             """
#             QFrame {
#                 background-color: #001F3F;
#                 border: 1px solid #e0e0e0;
#                 border-radius: 8px;
#                 padding: 0px;
#             }
#         """
#         )

# class StatusCard(QFrame):
#     def __init__(self, title, value, color="#6d200d", parent=None):
#         super().__init__(parent)
#         self.setFixedHeight(80)  # normal height

#         self.setStyleSheet(
#             f"""
#             QFrame {{
#                 border-left: 4px solid {color};
#                 border-radius: 6px;
#                 padding: 12px;
#                 margin: 4px;
#             }}
#         """
#         )

#         layout = QVBoxLayout(self)
#         layout.setSpacing(6)
#         layout.setContentsMargins(8, 8, 8, 8)

#         # Title label
#         title_label = QLabel(title)
#         title_label.setStyleSheet(
#             """
#             font-size: 14px; font-weight: 500; color: #757575; background: transparent;
#         """
#         )
#         title_label.setWordWrap(True)
#         title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

#         # Value label
#         self.value_label = QLabel(value)
#         self.value_label.setStyleSheet(
#             """
#             font-size: 16px; font-weight: 600; color: #212121; background: transparent;
#         """
#         )
#         self.value_label.setWordWrap(True)
#         self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

#         layout.addWidget(title_label)
#         layout.addWidget(self.value_label)

#     # Update value
#     def update_value(self, value):
#         self.value_label.setText(value)
# class SidebarButton(QPushButton):
#     def __init__(self, text, icon_text="", parent=None):
#         super().__init__(text, parent)
#         self.icon_text = icon_text
#         self.setCursor(Qt.PointingHandCursor)
#         self.setFixedHeight(45)
#         self.setStyleSheet(self.get_default_style())

#     def get_default_style(self):
#         return """
#             QPushButton {
#                 text-align: left;
#                 padding: 10px 15px;
#                 border: none;
#                 border-radius: 6px;
#                 background-color: transparent;
#                 color: #ffffff;
#                 font-size: 14px;
#                 font-weight: 500;
#             }
#             QPushButton:hover {
#                 background-color: #E3F2FD;
#                 color: #1976d2;
#             }
#             QPushButton:pressed {
#                 background-color: #E3F2FD;
#             }
#         """

#     def set_active(self, active=True):
#         if active:
#             self.setStyleSheet(
#                 """
#                 QPushButton {
#                     text-align: left;
#                     padding: 10px 15px;
#                     border: none;
#                     border-radius: 6px;
#                     background-color: #E3F2FD;
#                     color: #1976d2;
#                     font-size: 14px;
#                     font-weight: 600;
#                 }
#                 QPushButton:hover { background-color: #E3F2FD; }
#             """
#             )
#         else:
#             self.setStyleSheet(self.get_default_style())

# class CalendarDelegate(QStyledItemDelegate):
#     def paint(self, painter, option, index):
#         super().paint(painter, option, index)
#         date = index.data()
#         if not date:
#             return

#         rect = option.rect
#         text = str(date)
#         today = QDate.currentDate().day()
#         is_today = text.isdigit() and int(text) == today
#         is_selected = option.state & QStyle.State_Selected
#         is_hovered = option.state & QStyle.State_MouseOver

#         # Weekend detection (optional, you can adjust for actual weekday)
#         # row = index.row()  # if using QTableView for calendar
#         # is_weekend = (row % 7 == 0 or row % 7 == 6)

#         painter.save()
#         center = rect.center()
#         radius = min(rect.width(), rect.height()) // 2 - 4
#         accent = QColor("#0078D7")  # blue accent

#         # Background circle for today / selected / hover
#         if is_today and not is_selected:
#             painter.setBrush(QBrush(accent))
#             painter.setPen(Qt.NoPen)
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         elif is_selected:
#             painter.setBrush(QBrush(accent.lighter(150)))
#             painter.setPen(QPen(accent, 2))
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         elif is_hovered:
#             painter.setBrush(QBrush(QColor(0, 120, 215, 60)))
#             painter.setPen(Qt.NoPen)
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         else:
#             painter.setPen(QPen(QColor(50, 50, 50)))  # default text color
#             painter.setBrush(Qt.NoBrush)

#         # Draw text
#         painter.setFont(option.font)
#         painter.drawText(rect, Qt.AlignCenter, text)
#         painter.restore()

# def get_app_version():
#     try:
#         return importlib.metadata.version("FixHR")
#     except importlib.metadata.PackageNotFoundError:
#         return "1.0.0"

# class Sidebar(QFrame):
#     dashboard_clicked = pyqtSignal()
#     attendance_clicked = pyqtSignal()
#     employees_clicked = pyqtSignal()
#     reports_clicked = pyqtSignal()
#     settings_clicked = pyqtSignal()
#     date_selected = pyqtSignal(str)

#     def __init__(self, session, parent=None):
#         super().__init__(parent)
#         self.session = session
#         self.expanded_width = 280
#         self.collapsed_width = 60
#         self.is_collapsed = False
#         self.setFixedWidth(self.expanded_width)
#         self.setStyleSheet(
#             """
#             QFrame {
#                 background-color: #001F3F;
#             }
#         """
#         )
#         self.active_button = None
#         self.init_ui()

#     def init_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(0, 0, 0, 0)
#         main_layout.setSpacing(0)

#         top_bar = QFrame()
#         top_bar_layout = QHBoxLayout(top_bar)
#         top_bar_layout.setContentsMargins(10, 5, 10, 5)
#         top_bar_layout.setSpacing(0)

#         logo_frame = QFrame()
#         logo_layout = QVBoxLayout(logo_frame)
#         logo_layout.setContentsMargins(0, 0, 0, 0)
#         logo_layout.setSpacing(2)

#         # self.logo_label = QLabel("FixHR")
#         # self.logo_label.setStyleSheet(
#         #     "font-size: 20px; font-weight: 700; color: #FF8C00; background: transparent;"
#         # )
#         # self.logo_label.setAlignment(Qt.AlignLeft)
#         self.logo_label = QLabel()
#         self.logo_label.setAlignment(Qt.AlignLeft)

#         # Load your image
#         pixmap = QPixmap(resource_path("logo_dark.png"))  # replace with your image path
#         pixmap = pixmap.scaled(120, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#         self.logo_label.setPixmap(pixmap)

#         # Optional: resize the label to fit the image
#         self.logo_label.setFixedSize(pixmap.width(), pixmap.height())
#         self.logo_label.setStyleSheet("background: transparent;") 

#         self.version_label = QLabel(f"v{get_app_version()}")
#         self.version_label.setStyleSheet(
#             "font-size: 11px; color: #ffffff; background: transparent;"
#         )
#         self.version_label.setAlignment(Qt.AlignLeft)

#         logo_layout.addWidget(self.logo_label)
#         logo_layout.addWidget(self.version_label)
#         top_bar_layout.addWidget(logo_frame, alignment=Qt.AlignLeft)

#         top_bar_layout.addStretch()

#         self.toggle_btn = QToolButton()
#         self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
#         self.toggle_btn.setIconSize(QSize(28, 28))
#         self.toggle_btn.setCursor(Qt.PointingHandCursor)
#         self.toggle_btn.setStyleSheet(
#             """
#             QToolButton {
#                 border: none;
#                 background-color: rgba(255,255,255,0.1);
#                 border-radius: 15px;
#                 padding: 6px;
#                 color: white;
#             }
#             QToolButton:hover {
#                 background-color: rgba(255,255,255,0.25);
#             }
#         """
#         )
#         self.toggle_btn.clicked.connect(self.toggle_sidebar)
#         top_bar_layout.addWidget(self.toggle_btn, alignment=Qt.AlignRight)

#         main_layout.addWidget(top_bar)

#         scroll = QScrollArea(self)
#         scroll.setWidgetResizable(True)
#         scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

#         content = QWidget()
#         scroll.setWidget(content)

#         layout = QVBoxLayout(content)
#         layout.setSpacing(10)
#         layout.setContentsMargins(10, 20, 5, 20)
#         layout.setAlignment(Qt.AlignTop)

#         user_info_frame = QFrame()
#         user_info_frame.setStyleSheet("background: transparent;")
#         user_info_layout = QVBoxLayout(user_info_frame)
#         user_info_layout.setSpacing(6)
#         user_info_layout.setContentsMargins(0, 0, 0, 0)

#         user_avatar = QLabel("👤")  # ya user initials
#         user_avatar.setFixedSize(80, 80)
#         user_avatar.setAlignment(Qt.AlignCenter)
#         user_avatar.setStyleSheet("""
#             font-size: 60px;
#             background-color: #002F5E;
#             border-radius: 40px;
#             padding: 8px;
#             color: #F5F5F5;
#             border: 2px solid #004080;
#         """)

#         # Shadow effect
#         shadow = QGraphicsDropShadowEffect()
#         shadow.setBlurRadius(12)       # shadow blur
#         shadow.setXOffset(2)           # horizontal offset
#         shadow.setYOffset(2)           # vertical offset
#         shadow.setColor(QColor(0, 0, 0, 120))  # shadow color with opacity
#         user_avatar.setGraphicsEffect(shadow)

#         user_name = QLabel(f"Welcome, {self.session.get('name','User')}")
#         user_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent;")
#         user_name.setAlignment(Qt.AlignCenter)

#         user_role = QLabel("Admin" if is_logged_in() else "Guest")
#         user_role.setStyleSheet("font-size: 12px; color: #cccccc; background: transparent;")
#         user_role.setAlignment(Qt.AlignCenter)

#         user_info_layout.addWidget(user_avatar, alignment=Qt.AlignCenter)
#         user_info_layout.addWidget(user_name, alignment=Qt.AlignCenter)
#         user_info_layout.addWidget(user_role, alignment=Qt.AlignCenter)

#         layout.addWidget(user_info_frame, alignment=Qt.AlignHCenter)

#         layout.addSpacing(20)

#         self.nav_label = QLabel("NAVIGATION")
#         self.nav_label.setStyleSheet(
#             "font-size: 11px; font-weight: 600; color: #9e9e9e; margin-bottom: 10px; background: transparent;"
#         )
#         layout.addWidget(self.nav_label, alignment=Qt.AlignLeft)

#         self.nav_buttons = {}

#         if is_logged_in():
#             self.fetch_btn = QPushButton("Sync Employees")
#             self.fetch_btn.setCursor(QCursor(Qt.PointingHandCursor))
#             self.fetch_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
#             def add_shadow(button):
#                 shadow = QGraphicsDropShadowEffect()
#                 shadow.setBlurRadius(12)
#                 shadow.setXOffset(2)
#                 shadow.setYOffset(2)
#                 shadow.setColor(QColor(0, 0, 0, 100))
#                 button.setGraphicsEffect(shadow)

#             # Fetch Employees button
#             self.fetch_btn = QPushButton("Fetch Employees")
#             self.fetch_btn.setCursor(QCursor(Qt.PointingHandCursor))
#             self.fetch_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
#             self.fetch_btn.setStyleSheet("""
#                 QPushButton {
#                     background-color: #002F5E;
#                     color: white;
#                     border: none;
#                     padding: 8px 14px;
#                     border-radius: 6px;
#                 }
#                 QPushButton:hover {
#                     background-color: #004080;
#                 }
#                 QPushButton:pressed {
#                     background-color: #001F3F;
#                 }
#             """)
#             add_shadow(self.fetch_btn)
#             self.fetch_btn.clicked.connect(lambda: self.parent().fetch_employees())
#             layout.addWidget(self.fetch_btn, alignment=Qt.AlignLeft)

#             # Sync Attendance button
#             self.sync_btn = QPushButton("Sync Attendance")
#             self.sync_btn.setCursor(QCursor(Qt.PointingHandCursor))
#             self.sync_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
#             self.sync_btn.setStyleSheet("""
#                 QPushButton {
#                     background-color: #002F5E;
#                     color: white;
#                     border: none;
#                     padding: 8px 14px;
#                     border-radius: 6px;
#                 }
#                 QPushButton:hover {
#                     background-color: #004080;
#                 }
#                 QPushButton:pressed {
#                     background-color: #001F3F;
#                 }
#             """)
#             add_shadow(self.sync_btn)
#             self.sync_btn.clicked.connect(self.start_sync)
#             layout.addWidget(self.sync_btn, alignment=Qt.AlignLeft)

#         layout.addStretch()

#         # if is_logged_in():
#         self.cal_label = QLabel("CALENDAR")
#         self.cal_label.setStyleSheet(
#             "font-size: 11px; font-weight: 600; color: #9e9e9e; margin-bottom: 10px; background: transparent;"
#         )
#         layout.addWidget(self.cal_label, alignment=Qt.AlignLeft)

#         self.calendar = QCalendarWidget()
#         self.calendar.setGridVisible(True)
#         self.calendar.setStyleSheet(
#             """
#             QCalendarWidget {
#                 background-color: #001F3F;
#                 border: 1px solid #2c3e50;
#                 color: white;
#             }
#             QCalendarWidget QToolButton {
#                 color: white;
#                 font-size: 14px;
#                 background-color: #002F5E;
#                 border: none;
#                 margin: 1px;
#                 padding: 4px;
#             }
#             QCalendarWidget QMenu {
#                 background-color: #001F3F;
#                 color: white;
#                 border: 1px solid #2c3e50;
#             }
#             QCalendarWidget QMenu::item {
#                 background-color: #001F3F;
#                 color: white;
#                 padding: 5px 10px;
#             }
#             QCalendarWidget QMenu::item:selected {
#                 background-color: #004080;
#                 color: white;
#             }
#             QCalendarWidget QWidget {
#                 alternate-background-color: #001F3F;
#                 color: white;
#             }
#         """
#         )
#         self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
#         self.calendar.selectionChanged.connect(self.on_date_selected)

#         view = self.calendar.findChild(QTableView)
#         if view:
#             view.setItemDelegate(CalendarDelegate(view))

#         layout.addWidget(self.calendar, alignment=Qt.AlignLeft)

#         main_layout.addWidget(scroll)

#     def start_sync(self):
#         try:
#             start_background_sync()
#             QMessageBox.information(self, "Success", "Attendance sync started successfully")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to start attendance sync: {str(e)}")

#     def on_date_selected(self):
#         selected_date = self.calendar.selectedDate().toString("dd-MM-yyyy")
#         self.date_selected.emit(selected_date)

#     def toggle_sidebar(self):
#         if self.is_collapsed:
#             self.setFixedWidth(self.expanded_width)
#             self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
#             self.logo_label.show()
#             self.version_label.show()
#             self.nav_label.show()
#             if hasattr(self, 'cal_label'):
#                 self.cal_label.show()
#             if hasattr(self, 'calendar'):
#                 self.calendar.show()
#             if hasattr(self, 'fetch_btn'):
#                 self.fetch_btn.show()
#             if hasattr(self, 'sync_btn'):
#                 self.sync_btn.show()
#             self.is_collapsed = False
#         else:
#             self.setFixedWidth(self.collapsed_width)
#             self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
#             self.logo_label.hide()
#             self.version_label.hide()
#             self.nav_label.hide()
#             if hasattr(self, 'cal_label'):
#                 self.cal_label.hide()
#             if hasattr(self, 'calendar'):
#                 self.calendar.hide()
#             if hasattr(self, 'fetch_btn'):
#                 self.fetch_btn.hide()
#             if hasattr(self, 'sync_btn'):
#                 self.sync_btn.hide()
#             self.is_collapsed = True

#     def set_active_button(self, button_name):
#         if self.active_button:
#             self.active_button.set_active(False)
#         if button_name in self.nav_buttons:
#             self.nav_buttons[button_name].set_active(True)
#             self.active_button = self.nav_buttons[button_name]

# def resource_path(relative_path):
#     try:
#         base_path = sys._MEIPASS
#     except AttributeError:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)

# class LoginDialog(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Login")
#         self.setFixedSize(800, 600)
#         bg_img = resource_path("background-img.jpg")
#         bg_img = bg_img.replace("\\", "/")
#         self.setStyleSheet(
#             f"""
#             QDialog {{
#                 background-image: url({bg_img});
#                 background-position: center;
#                 background-repeat: no-repeat;
#                 font-family: 'Segoe UI', sans-serif;
#             }}
#         """
#         )
#         main_layout = QVBoxLayout()
#         main_layout.setContentsMargins(100, 20, 100, 100)
#         main_layout.setSpacing(30)
#         container = QFrame()
#         container.setStyleSheet(
#             """
#             QFrame {
#                 border-radius: 15px;
#             }
#         """
#         )
#         container_layout = QVBoxLayout(container)
#         container_layout.setContentsMargins(40, 10, 40, 40)
#         container_layout.setSpacing(15)
#         user_icon = QLabel()
#         user_icon.setFixedSize(120, 120)
#         pixmap = QPixmap(120, 120)
#         pixmap.fill(Qt.transparent)
#         painter = QPainter(pixmap)
#         painter.setRenderHint(QPainter.Antialiasing)
#         pen = QPen(QColor(255, 255, 255), 3)
#         painter.setPen(pen)
#         painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
#         painter.drawEllipse(10, 10, 100, 100)
#         painter.setPen(QPen(QColor(255, 255, 255), 2))
#         painter.setBrush(QBrush(QColor(255, 255, 255)))
#         painter.drawEllipse(45, 30, 30, 30)
#         painter.setPen(QPen(QColor(255, 255, 255), 6))
#         painter.drawArc(35, 65, 50, 35, 0, 180 * 16)
#         painter.end()
#         user_icon.setPixmap(pixmap)
#         user_icon.setAlignment(Qt.AlignCenter)
#         container_layout.addWidget(user_icon, alignment=Qt.AlignCenter)
#         container_layout.addSpacing(10)
#         title_label = QLabel("FixHr User")
#         title_label.setStyleSheet(
#             """
#             QLabel {
#                 font-size: 32px;
#                 font-weight: bold;
#                 color: #FFFFFF;
#                 padding-bottom: 10px;
#             }
#         """
#         )
#         title_label.setAlignment(Qt.AlignCenter)
#         container_layout.addWidget(title_label)
#         username_layout = QVBoxLayout()
#         username_label = QLabel("User name:")
#         username_label.setStyleSheet(
#             "font-size: 18px; color: #FFFFFF; margin-bottom: 5px;"
#         )
#         username_label.setAlignment(Qt.AlignLeft)
#         self.username_input = QLineEdit()
#         self.username_input.setStyleSheet(
#             """
#             QLineEdit {
#                 font-size: 18px;
#                 padding: 12px;
#                 border: 2px solid #ddd;
#                 border-radius: 8px;
#                 min-width: 250px;
#                 background-color: transparent;
#                 color: white;
#             }
#         """
#         )
#         username_layout.addWidget(username_label)
#         username_layout.addWidget(self.username_input)
#         container_layout.addLayout(username_layout)
#         password_layout = QVBoxLayout()
#         password_label = QLabel("Password:")
#         password_label.setStyleSheet(
#             "font-size: 18px; color: #FFFFFF; margin-bottom: 5px;"
#         )
#         password_label.setAlignment(Qt.AlignLeft)
#         self.password_input = QLineEdit()
#         self.password_input.setEchoMode(QLineEdit.Password)
#         self.password_input.setStyleSheet(
#             """
#             QLineEdit {
#                 font-size: 18px;
#                 padding: 12px;
#                 border: 2px solid #ddd;
#                 border-radius: 8px;
#                 min-width: 250px;
#                 background-color: transparent;
#                 color: white;
#             }
#         """
#         )
#         password_layout.addWidget(password_label)
#         password_layout.addWidget(self.password_input)
#         container_layout.addLayout(password_layout)
#         login_btn = QPushButton("Login")
#         login_btn.setStyleSheet(
#             """
#             QPushButton {
#                 font-size: 20px;
#                 font-weight: bold;
#                 color: white;
#                 background-color: transparent;
#                 border: 2px solid #3f51b5;
#                 border-radius: 10px;
#                 padding: 15px 30px;
#                 min-width: 150px;
#             }
#             QPushButton:hover {
#                 border: 2px solid #354497;
#             }
#         """
#         )
#         login_btn.clicked.connect(self.accept)
#         container_layout.addWidget(login_btn, alignment=Qt.AlignCenter)
#         main_layout.addWidget(container)
#         self.setLayout(main_layout)

#     def get_credentials(self):
#         return self.username_input.text(), self.password_input.text()

# class AttendanceApp(QWidget):
#     def __init__(self, session=None):
#         super().__init__()
#         self.session = session or {"name": "Guest"}
#         self.setWindowTitle("FixHR - Face Recognition Attendance System")
#         self.setGeometry(50, 50, 1800, 1000)
#         self.setStyleSheet(
#             """
#             QWidget { background-color: #001F3F; font-family: 'Segoe UI','Roboto',sans-serif; color: #ffffff; }
#         """
#         )
#         self.setWindowIcon(QIcon(resource_path("fix_hr_prod_logo.png")))
#         self.liveness_detector_loaded = False
#         self.detect_and_predict = None
#         self.fetch_thread = None
#         self.liveness_loader_thread = None
#         self.detect_worker_running = False
#         self._detect_worker = None
#         self.attendance_data = []
#         self.cap = None
#         self.init_ui()
#         self.init_timers()
#         self.load_liveness_detector_async()
#         self.backup_manager = BackupManager(
#             db_path=resource_path("employees.db"),
#         )
#         if is_logged_in():
#             self.session = load_session()
#             self.show_admin_view()
#             print("Existing session loaded - Admin view activated")
#         else:
#             self.show_guest_view()
#             print("No session found - Guest view activated")

#     def show_admin_view(self):
#         self.right_panel.setVisible(True)
#         self.admin_login_btn.setText("Admin: Logged In")
#         self.admin_login_btn.setStyleSheet(
#             """
#             QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #4caf50; border: none; border-radius: 4px; padding: 8px 16px; }
#             QPushButton:hover { background-color: #388e3c; }
#             """
#         )
#         # self.admin_login_btn.setVisible(False)
#         self.logout_btn.setVisible(True)
#         self.load_attendance_logs()
#         new_sidebar = Sidebar(self.session)
#         new_sidebar.date_selected.connect(self.update_table_by_date)
#         self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
#         self.sidebar = new_sidebar
#         self.reset_face_detection_layout()
#         self.data_refresh_timer.start(10000)  # Start the refresh timer
#         self.left_panel.update()
#         self.right_panel.update()

#     def show_guest_view(self):
#         """Enhanced show_guest_view method"""
#         self.right_panel.setVisible(False)
#         self.admin_login_btn.setText("Admin Login")
#         self.admin_login_btn.setStyleSheet(
#             """
#             QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
#             QPushButton:hover { background-color: #303f9f; }
#             """
#         )
#         self.logout_btn.setVisible(False)
#         self.employee_card.update_value("[Employee Name]")
#         self.data_refresh_timer.stop()  # Stop the refresh timer
#         self.update_face_detection_layout()
        


#     def create_circular_mask(self, width, height):
#         region = QRegion(0, 0, width, height, QRegion.Ellipse)
#         return region

#     def create_rectangular_mask(self, width, height):
#         region = QRegion(0, 0, width, height, QRegion.Rectangle)
#         return region

#     def closeEvent(self, event):
#         if hasattr(self, "backup_manager"):
#             self.backup_manager.stop()
#         if hasattr(self, "cap") and self.cap is not None:
#             self.cap.release()
#         if hasattr(self, "timer"):
#             self.timer.stop()
#         if hasattr(self, "detect_timer"):
#             self.detect_timer.stop()
#         if hasattr(self, "data_refresh_timer"):
#             self.data_refresh_timer.stop()
#         if hasattr(self, "fetch_thread") and self.fetch_thread:
#             self.fetch_thread.quit()
#             self.fetch_thread.wait()
#         if hasattr(self, "liveness_loader_thread") and self.liveness_loader_thread:
#             self.liveness_loader_thread.quit()
#             self.liveness_loader_thread.wait()
#         event.accept()

#     def load_liveness_detector_async(self):
#         if self.liveness_loader_thread and self.liveness_loader_thread.isRunning():
#             return
#         self.start_btn.setEnabled(False)
#         self.liveness_loader_thread = LivenessLoaderThread()
#         self.liveness_loader_thread.finished.connect(self.on_liveness_detector_loaded)
#         self.liveness_loader_thread.start()

#     def on_liveness_detector_loaded(self, success, message, detector_function):
#         if success:
#             self.detect_and_predict = detector_function
#             self.liveness_detector_loaded = True
#             self.start_btn.setEnabled(True)
#         else:
#             self.liveness_detector_loaded = False
#             self.start_btn.setEnabled(False)
#             print("Detector failed to load")
#             QMessageBox.critical(
#                 self, "Error", f"Failed to load liveness detector: {message}"
#             )

#     def fetch_employees(self):
#         if not is_logged_in():
#             QMessageBox.warning(self, "Access Denied", "Please login first to fetch employees.")
#             return
#         if self.fetch_thread and self.fetch_thread.isRunning():
#             QMessageBox.information(
#                 self, "Info", "Employee fetch is already in progress..."
#             )
#             return
#         self.sidebar.fetch_btn.setEnabled(False)
#         self.sidebar.fetch_btn.setText("Fetching...")
#         self.fetch_thread = FetchThread(self.session.get("token", ""))
#         self.fetch_thread.finished.connect(
#             lambda success, msg: self.on_fetch_completed(success, msg)
#         )
#         self.fetch_thread.start()

#     def on_fetch_completed(self, success, message):
#         if hasattr(self.sidebar, 'fetch_btn'):
#             self.sidebar.fetch_btn.setEnabled(True)
#             self.sidebar.fetch_btn.setText("Fetch Employees")
#         if success:
#             if self.liveness_detector_loaded and hasattr(self, "detect_and_predict"):
#                 try:
#                     from recognition import force_rebuild_index
#                     rebuild_success = force_rebuild_index()
#                     if rebuild_success:
#                         print("Ready - Faces loaded")
#                     else:
#                         print("Ready - No face images")
#                 except Exception:
#                     print("Ready - Index rebuild failed")
#             QMessageBox.information(self, "Success", message)
#         else:
#             print("Fetch failed")
#             QMessageBox.critical(self, "Error", f"Failed to fetch employees: {message}")

#     def logout(self):
#         reply = QMessageBox.question(
#             self,
#             "Logout",
#             "Are you sure you want to logout?",
#             QMessageBox.Yes | QMessageBox.No,
#             QMessageBox.No,
#         )
#         if reply == QMessageBox.Yes:
#             clear_session()
#             self.session = {"name": "Guest"}
#             self.data_refresh_timer.stop()  # Stop the refresh timer
#             self.show_guest_view()
#             new_sidebar = Sidebar(self.session)
#             new_sidebar.date_selected.connect(self.update_table_by_date)
#             main_layout = self.layout()
#             old_sidebar = main_layout.itemAt(0).widget()
#             main_layout.replaceWidget(old_sidebar, new_sidebar)
#             old_sidebar.deleteLater()
#             self.sidebar = new_sidebar
#             QMessageBox.information(self, "Success", "Successfully logged out!")
#             print("Logged out successfully - showing guest view with centered face detection")

#     def update_face_detection_layout(self):
#         """Enhanced guest view layout with better styling and date/time"""
#         self.content_layout.setAlignment(self.left_panel, Qt.AlignTop | Qt.AlignCenter)
#         self.left_panel.setFixedWidth(1200)
#         self.left_panel.setFixedHeight(900)
        
#         # Enhanced styling for guest view
#         self.left_panel.setStyleSheet("""
#             QFrame { 
#                 border: 2px solid #dee2e6;
#                 border-radius: 20px;
#             }
#         """)
        
#         # Add shadow effect to the entire panel
#         panel_shadow = QGraphicsDropShadowEffect()
#         panel_shadow.setBlurRadius(25)
#         panel_shadow.setXOffset(5)
#         panel_shadow.setYOffset(5)
#         panel_shadow.setColor(QColor(0, 0, 0, 60))
#         self.left_panel.setGraphicsEffect(panel_shadow)
        
#         # Enhanced camera container styling - positioned in center-left
#         self.camera_container.setFixedSize(650, 450)
#         self.video_label.setFixedSize(630, 430)
#         self.video_label.setMask(self.create_rectangular_mask(630, 430))
        
#         # Position camera container in center-left area
#         self.camera_container.move(50, 200)
        
#         self.camera_container.setStyleSheet("""
#             QFrame {
#                 background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
#                     stop:0 #ffffff, stop:1 #f8f9fa);
#                 border-radius: 20px;
#             }
#         """)
        
#         # Camera shadow effect
#         camera_shadow = QGraphicsDropShadowEffect()
#         camera_shadow.setBlurRadius(20)
#         camera_shadow.setXOffset(3)
#         camera_shadow.setYOffset(3)
#         camera_shadow.setColor(QColor(0, 123, 255, 80))
#         self.camera_container.setGraphicsEffect(camera_shadow)
        
#         # Enhanced live indicator positioning - on camera container
#         self.live_label.move(60, 170)
#         self.live_label.setStyleSheet("""
#             font-size: 18px;
#             font-weight: 700;
#             color: #28a745;
#             border: none;
#             background: rgba(255, 255, 255, 0.9);
#             padding: 8px 15px;
#             border-radius: 12px;
#         """)
        
#         self.live_dot.move(50, 170)
#         self.live_dot.setStyleSheet("""
#             QLabel {
#                 background-color: #28a745;
#                 border-radius: 15px;
#                 border: 4px solid #d4edda;
#             }
#         """)
#         self.live_dot.setFixedSize(30, 30)
        
#         # Position elements in right side - no overlap with camera
#         self.employee_card.setFixedSize(250, 100)
#         self.employee_card.move(750, 50)
        
#         # Enhanced device info positioning - bottom left
#         self.device_info_label.move(50, 700)
#         self.device_info_label.setStyleSheet("""
#             font-size: 14px; 
#             font-weight: 600; 
#             color: #495057; 
#             border: none; 
#             margin-top: 5px;
#             background: rgba(255, 255, 255, 0.9);
#             padding: 15px;
#             border-radius: 12px;
#             border: 1px solid #dee2e6;
#         """)
        
#         # Create and position date/time labels for guest view
#         self.create_guest_datetime_display()
        
#         print("Enhanced guest view with better styling and date/time display")

#     def create_guest_datetime_display(self):
#         """Simple date and time display at the top"""
#         # Clean up existing widgets if already created
#         if hasattr(self, 'guest_date_label'):
#             self.guest_date_label.deleteLater()
#         if hasattr(self, 'guest_time_label'):
#             self.guest_time_label.deleteLater()

#         # Date label
#         panel_width = self.left_panel.width()
#         self.guest_date_label = QLabel(self.left_panel)
#         self.guest_date_label.setGeometry((panel_width - 300) // 2, 10, 300, 30) # top left
#         self.guest_date_label.setStyleSheet("""
#             QLabel {
#                 font-size: 14px;
#                 font-weight: bold;
#                 color: #007bff;
#                 background: transparent;
#             }
#         """)
#         self.guest_date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

#         # Time label
#         self.guest_time_label = QLabel(self.left_panel)
#         self.guest_time_label.setGeometry((panel_width - 300) // 2, 45, 300, 35)  # just below date
#         self.guest_time_label.setStyleSheet("""
#             QLabel {
#                 font-size: 18px;
#                 font-weight: 600;
#                 color: #28a745;
#                 background: transparent;
#             }
#         """)
#         self.guest_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

#         # Update once immediately
#         self.update_guest_datetime()


#     def update_guest_datetime(self):
#         """Update date and time for guest view"""
#         if hasattr(self, 'guest_date_label') and hasattr(self, 'guest_time_label'):
#             now = datetime.datetime.now()
#             self.guest_date_label.setText(f"Date: {now.strftime('%d-%m-%Y')}")
#             self.guest_time_label.setText(f"{now.strftime('%I:%M:%S %p')}")

#     def update_time(self):
#         """Enhanced update_time method to handle both admin and guest views"""
#         now = datetime.datetime.now()
        
#         # Update admin view time labels (existing functionality)
#         if hasattr(self, 'time_label') and hasattr(self, 'date_label'):
#             self.time_label.setText(now.strftime("%I:%M:%S"))
#             self.date_label.setText(f"Date: {now.strftime('%d-%m-%y')}")
        
#         # Update guest view time labels (new functionality)
#         if hasattr(self, 'guest_date_label') and hasattr(self, 'guest_time_label'):
#             self.update_guest_datetime()


#     def admin_login(self):
#         if is_logged_in():
#             reply = QMessageBox.question(
#                 self,
#                 "Session Active",
#                 "An admin session is already active. Do you want to log out the current session and log in again?",
#                 QMessageBox.Yes | QMessageBox.No,
#                 QMessageBox.No,
#             )
#             if reply == QMessageBox.Yes:
#                 clear_session()
#                 self.session = {"name": "Guest"}
#                 self.data_refresh_timer.stop()  # Stop the refresh timer
#                 self.show_guest_view()
#                 new_sidebar = Sidebar(self.session)
#                 new_sidebar.date_selected.connect(self.update_table_by_date)
#                 self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
#                 self.sidebar = new_sidebar
#             else:
#                 return

#         dialog = LoginDialog()
#         if dialog.exec_() == QDialog.Accepted:
#             email, password = dialog.get_credentials()
#             result = login_fixhr(email, password)
#             if result["status"] == "success":
#                 self.session = result["data"]
#                 self.show_admin_view()
#                 QMessageBox.information(self, "Success", "Admin login successful")
#                 print("Admin logged in - showing right panel with four-box overview and daily attendance")
#             else:
#                 self.show_guest_view()
#                 QMessageBox.critical(
#                     self, "Login Failed", result.get("message", "Unknown error")
#                 )
#         else:
#             self.show_guest_view()

#     def reset_face_detection_layout(self):
#         self.content_layout.setAlignment(self.left_panel, Qt.AlignLeft)
#         self.left_panel.setFixedWidth(500)
#         self.left_panel.setMaximumHeight(16777215)
#         self.camera_container.setFixedSize(350, 350)
#         self.video_label.setFixedSize(330, 330)
#         self.video_label.setMask(self.create_circular_mask(330, 330))
#         self.live_label.move(10, 20)
#         self.live_dot.move(0, 20)
#         self.employee_card.move(150, 370)
#         self.device_info_label.move(10, 400)
#         self.left_panel.update()
#         print("Left panel reset to vertical layout for admin")

#     def create_overview_cards(self):
#         for i in reversed(range(self.overview_grid.count())):
#             widget = self.overview_grid.itemAt(i).widget()
#             if widget:
#                 widget.setParent(None)
#         summary = get_daily_attendance_summary()
#         total_emp = get_employee_count()
#         present_today = summary["checked_in_only"] + summary["completed_attendance"]
#         last_sync_str, next_sync_str = get_sync_status_overview()
#         self.overview_grid.addWidget(
#             self.make_overview_card(
#                 "Total Employees",
#                 str(total_emp),
#                 "All active staff members",
#                 "#E3F2FD",
#                 "#1E88E5",
#                 "👥",
#             ),
#             0,
#             0,
#         )
#         self.overview_grid.addWidget(
#             self.make_overview_card(
#                 "Present Today",
#                 str(present_today),
#                 "Checked-in employees",
#                 "#E8F5E9",
#                 "#2E7D32",
#                 "✅",
#             ),
#             0,
#             1,
#         )
#         self.overview_grid.addWidget(
#             self.make_overview_card(
#                 "Last DB Sync",
#                 last_sync_str,
#                 "",
#                 "#FFF8E1",
#                 "#FF8C00",
#                 "🗄️",
#                 compact=True,
#             ),
#             0,
#             2,
#         )
#         self.overview_grid.addWidget(
#             self.make_overview_card(
#                 "Next Sync",
#                 next_sync_str,
#                 "",
#                 "#FCE4EC",
#                 "#D81B60",
#                 "⏳",
#                 compact=True,
#             ),
#             0,
#             3,
#         )

#     def make_overview_card(self, title, number, sub, bg, fg, icon_text, compact=False):
#         card = QFrame()
        
#         # Solid background (pehle ka color)
#         card.setStyleSheet(f"""
#             QFrame {{
#                 background-color: {bg};
#                 border-radius: 14px;
#             }}
#         """)

#         # Shadow effect for 3D
#         shadow = QGraphicsDropShadowEffect()
#         shadow.setBlurRadius(35)
#         shadow.setXOffset(0)
#         shadow.setYOffset(8)
#         shadow.setColor(QColor(0, 0, 0, 120))
#         card.setGraphicsEffect(shadow)

#         # Hover animation
#         anim = QPropertyAnimation(shadow, b"blurRadius", card)
#         anim.setDuration(250)
#         anim.setEasingCurve(QEasingCurve.OutQuad)

#         def enterEvent(event):
#             anim.stop()
#             anim.setStartValue(shadow.blurRadius())
#             anim.setEndValue(60)  # stronger shadow on hover
#             anim.start()
#             card.move(card.x(), card.y() - 6)  # lift card
#             event.accept()

#         def leaveEvent(event):
#             anim.stop()
#             anim.setStartValue(shadow.blurRadius())
#             anim.setEndValue(35)  # back to normal
#             anim.start()
#             card.move(card.x(), card.y() + 6)  # move down
#             event.accept()

#         card.enterEvent = enterEvent
#         card.leaveEvent = leaveEvent

#         # Layouts
#         v = QVBoxLayout(card)
#         v.setContentsMargins(16, 16, 16, 16)
#         v.setSpacing(8)

#         # Icon
#         icon = QLabel(icon_text)
#         icon.setAlignment(Qt.AlignCenter)
#         icon.setFixedSize(40, 40)
#         icon.setStyleSheet(f"""
#             QLabel {{
#                 background: rgba(255,255,255,0.8);
#                 border-radius: 20px;
#                 font-size: 18px;
#                 color: {fg};
#                 font-weight: 700;
#             }}
#         """)

#         # Labels
#         if compact:
#             t = QLabel(title)
#             t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
#             n = QLabel(str(number))
#             n.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 500;")
#             s = QLabel(sub)
#             s.setStyleSheet(f"font-size: 11px; color: {fg};")
#         else:
#             t = QLabel(title)
#             t.setStyleSheet(f"font-size: 14px; color: {fg}; font-weight: 600;")
#             n = QLabel(str(number))
#             n.setStyleSheet(f"font-size: 26px; color: {fg}; font-weight: 900;")
#             s = QLabel(sub)
#             s.setStyleSheet(f"font-size: 12px; color: {fg};")
#             t.setWordWrap(True)
#             n.setWordWrap(True)
#             s.setWordWrap(True)

#         # Top layout
#         top_h = QHBoxLayout()
#         top_h.setSpacing(10)
#         top_h.addWidget(icon, 0, Qt.AlignLeft)
#         top_h.addWidget(t, 0, Qt.AlignVCenter)
#         top_h.addStretch()
#         v.addLayout(top_h)
#         v.addWidget(n)
#         if sub:
#             v.addWidget(s)

#         return card

#     def get_pending_sync_count(self):
#         return 8  # Replace with actual logic to count unsynced records

#     # def refresh_data(self):
#     #     if not is_logged_in():
#     #         return
#     #     try:
#     #         self.create_overview_cards()
#     #         current_date = self.date_label.text().replace("Date: ", "") if hasattr(self, 'date_label') else ""
#     #         if current_date == "--- --- --" or not current_date:
#     #             current_date = datetime.datetime.now().strftime("%d-%m-%y")
#     #         # self.update_table_by_date(current_date)
#     #         self.alert_msg.setText(f"{self.get_pending_sync_count()} records pending sync")
#     #     except Exception as e:
#     #         print(f"Error refreshing data: {e}")
#     def refresh_data(self):
#         if not is_logged_in():
#             return
#         try:
#             # Only refresh the overview cards
#             self.create_overview_cards()
#             # Update the alert message for pending sync count
#             self.alert_msg.setText(f"{self.get_pending_sync_count()} records pending sync")
#         except Exception as e:
#             print(f"Error refreshing cards: {e}")

#     def update_attendance_table(self):
#         self.daily_table.setRowCount(0)
#         emp_code = self.session.get("employee_id", None)
#         for entry in self.attendance_data:
#             if is_logged_in() or (emp_code and entry[0][0] == str(emp_code)):
#                 row_pos = self.daily_table.rowCount()
#                 self.daily_table.insertRow(row_pos)
#                 for col, (text, font, color) in enumerate(entry):
#                     item = QTableWidgetItem(text)
#                     item.setFont(font)
#                     item.setForeground(QColor(color))
#                     self.daily_table.setItem(row_pos, col, item)
#         self.daily_table.scrollToTop()

#     def toggle_blink(self):
#         if self.online_status:
#             if self.blink_state:
#                 self.live_dot.setStyleSheet(
#                     """
#                     QLabel {
#                         background-color: #4caf50;
#                         border-radius: 12px;
#                         border: 3px solid #a5d6a7;
#                     }
#                 """
#                 )
#             else:
#                 self.live_dot.setStyleSheet(
#                     """
#                     QLabel {
#                         background-color: transparent;
#                         border-radius: 12px;
#                         border: 3px solid #a5d6a7;
#                     }
#                 """
#                 )
#         else:
#             self.live_dot.setStyleSheet(
#                 """
#                 QLabel {
#                     background-color: red;
#                     border-radius: 12px;
#                     border: 3px solid #ef9a9a;
#                 }
#             """
#             )
#         self.blink_state = not self.blink_state

#     def update_internet_status(self):
#         online = is_internet_available()
#         self.online_status = online
#         self.live_label.setText("Live" if online else "Offline")
#         self.device_info_label.setText(
#             f"Device Name: {self.device_info_data['device_name']}\n"
#             f"Device Model: {self.device_info_data['device_model']}\n"
#             f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
#             f"Internet Status: {'Online' if online else 'Offline'}"
#         )

#     def update_camera_border(self, recognition_status):
#         self.camera_container.setStyleSheet(
#             "QFrame { background: transparent; border: none; border-radius: 200px; }"
#         )
#         glow = QGraphicsDropShadowEffect(self.camera_container)
#         glow.setOffset(0, 0)
#         glow.setBlurRadius(40)
#         if recognition_status == "recognized":
#             color = QColor("#4caf50")
#         elif recognition_status == "detecting":
#             color = QColor("#ff9800")
#         elif recognition_status == "failed":
#             color = QColor("#f44336")
#         else:
#             color = QColor("#3f51b5")
#         glow.setColor(color)
#         self.camera_container.setGraphicsEffect(glow)
#         self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
#         self.glow_animation.setStartValue(20)
#         self.glow_animation.setEndValue(80)
#         self.glow_animation.setDuration(1000)
#         self.glow_animation.setLoopCount(-1)
#         self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
#         self.glow_animation.start()

#     def reset_camera_border_after_delay(self):
#         QTimer.singleShot(3000, lambda: self.update_camera_border("default"))

#     def on_recognition_success(self, employee_name):
#         self.employee_card.update_value(employee_name)
#         self.update_camera_border("recognized")
#         self.reset_camera_border_after_delay()
#         print(f"Recognition successful: {employee_name}")

#     def on_recognition_failed(self):
#         self.employee_card.update_value("Unknown Person")
#         self.update_camera_border("failed")
#         self.reset_camera_border_after_delay()
#         print("Recognition failed")

#     def on_detection_started(self):
#         self.update_camera_border("detecting")
#         print("Detection started")

#     def on_detection_stopped(self):
#         self.update_camera_border("default")
#         print("Detection stopped")

#     def init_ui(self):
#         main_layout = QHBoxLayout(self)
#         main_layout.setSpacing(0)
#         main_layout.setContentsMargins(0, 0, 0, 0)

#         self.sidebar = Sidebar(self.session)
#         self.sidebar.date_selected.connect(self.update_table_by_date)
#         main_layout.addWidget(self.sidebar)

#         content_widget = QWidget()
#         content_widget.setStyleSheet("background-color: #f5f5f5;")
#         self.main_content_layout = QVBoxLayout(content_widget)
#         self.main_content_layout.setSpacing(0)
#         self.main_content_layout.setContentsMargins(0, 0, 0, 0)

#         header_card = ModernCard()
#         header_card.setMinimumHeight(60)
#         header_card.setStyleSheet(
#             """
#             QFrame { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 0px; }
#         """
#         )
#         header_layout = QHBoxLayout(header_card)
#         header_layout.setContentsMargins(10, 0, 10, 0)
#         header_layout.setSpacing(16)

#         header_title = QLabel("Face Recognition Attendance System")
#         header_title.setStyleSheet(
#             "font-size: 22px; font-weight: 600; color: #ff9800; background: transparent; padding-top: 5px;"
#         )
#         header_layout.addWidget(header_title, 0, Qt.AlignTop | Qt.AlignLeft)

#         self.admin_login_btn = QPushButton("Admin Login")
#         self.admin_login_btn.setCursor(Qt.PointingHandCursor)
#         self.admin_login_btn.setFixedHeight(32)
#         self.admin_login_btn.setStyleSheet(
#             """
#             QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; margin-top: 5px; }
#             QPushButton:hover { background-color: #303f9f; }
#         """
#         )
#         self.admin_login_btn.clicked.connect(self.admin_login)
#         header_layout.addStretch()
#         header_layout.addWidget(self.admin_login_btn, 0, Qt.AlignTop | Qt.AlignRight)

#         self.logout_btn = QPushButton("Logout")
#         self.logout_btn.setCursor(Qt.PointingHandCursor)
#         self.logout_btn.setFixedHeight(32)
#         self.logout_btn.setStyleSheet(
#  """
#             QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #f44336; border: none; border-radius: 4px; padding: 8px 16px; }
#             QPushButton:hover { background-color: #d32f2f; }
#             """
#         )
#         self.logout_btn.clicked.connect(self.logout)
#         header_layout.addWidget(self.logout_btn, 0, Qt.AlignTop | Qt.AlignRight)
#         self.logout_btn.setVisible(False)

#         self.main_content_layout.addWidget(header_card)

#         self.content_layout = QHBoxLayout()
#         self.content_layout.setSpacing(8)

#         self.left_panel = QFrame()
#         self.left_panel.setFixedWidth(500)
#         self.left_panel.setStyleSheet(
#             """
#             QFrame { background-color: #ffffff; border: none; }
#         """
#         )
#         left_layout = QVBoxLayout(self.left_panel)
#         left_layout.setContentsMargins(8, 0, 8, 8)
#         left_layout.setSpacing(0)

#         header_row = QHBoxLayout()
#         header_row.setContentsMargins(0, 0, 0, 0)
#         header_row.setSpacing(4)

#         self.live_dot = QLabel()
#         self.live_dot.setFixedSize(24, 24)
#         self.live_dot.setStyleSheet(
#             """
#             QLabel {
#                 background-color: #4caf50;
#                 border-radius: 12px;
#                 border: 3px solid #a5d6a7;
#             }
#         """
#         )
#         self.live_label = QLabel("Live")
#         self.live_label.setStyleSheet(
#             """
#             font-size: 18px;
#             font-weight: 600;
#             color: #212121;
#             border: none;
#             margin-top: 0px;
#         """
#         )
#         self.live_label.setAlignment(Qt.AlignVCenter)

#         live_header = QHBoxLayout()
#         live_header.setContentsMargins(0, 0, 0, 0)
#         live_header.setSpacing(6)
#         live_header.addWidget(self.live_dot, 0, Qt.AlignVCenter)
#         live_header.addWidget(self.live_label, 0, Qt.AlignVCenter)

#         self.blink_state = True
#         self.online_status = True
#         self.blink_timer = QTimer()
#         self.blink_timer.timeout.connect(self.toggle_blink)
#         self.blink_timer.start(600)
#         self.internet_timer = QTimer()
#         self.internet_timer.timeout.connect(self.update_internet_status)
#         self.internet_timer.start(5000)

#         self.employee_card = StatusCard("Employee", "[Employee Name]", "#4caf50")
#         self.employee_card.setFixedWidth(250)
#         header_row.addLayout(live_header)
#         header_row.addStretch()
#         header_row.addWidget(self.employee_card)
#         left_layout.addLayout(header_row)
#         left_layout.addSpacing(10)

#         self.camera_container = QFrame()
#         self.camera_container.setFixedSize(350, 350)
#         self.camera_container.setStyleSheet(
#             "QFrame { background: transparent; border-radius: 175px; }"
#         )
#         camera_layout = QVBoxLayout(self.camera_container)
#         camera_layout.setContentsMargins(10, 10, 10, 10)
#         self.video_label = QLabel("Waiting for iVCam connection")
#         self.video_label.setFixedSize(330, 330)
#         self.video_label.setAlignment(Qt.AlignCenter)
#         self.video_label.setWordWrap(True)
#         self.video_label.setStyleSheet(
#             "QLabel { background-color: transparent; border: none; }"
#         )
#         self.video_label.setMask(self.create_circular_mask(330, 330))
#         camera_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
#         left_layout.addWidget(self.camera_container, alignment=Qt.AlignCenter)
#         left_layout.addSpacing(10)

#         self.device_info_data = get_device_info()
#         self.device_info_label = QLabel(
#             f"Device Name: {self.device_info_data['device_name']}\n"
#             f"Device Model: {self.device_info_data['device_model']}\n"
#             f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
#             f"Internet Status: {self.device_info_data.get('internet_status','Unknown')}"
#         )
#         self.device_info_label.setStyleSheet(
#             "font-size: 14px; font-weight: 500; color: #212121; border: none; margin-top: 5px;"
#         )
#         self.device_info_label.setWordWrap(True)
#         left_layout.addWidget(self.device_info_label)
#         left_layout.addSpacing(10)

#         button_layout = QHBoxLayout()
#         button_layout.setContentsMargins(0, 5, 0, 0)
#         button_layout.setSpacing(10)

#         self.start_btn = QPushButton("Start Detection")
#         self.start_btn.setCursor(Qt.PointingHandCursor)
#         self.start_btn.setFixedHeight(48)
#         self.start_btn.setStyleSheet(
#             """
#             QPushButton {
#                 font-size: 14px;
#                 font-weight: 500;
#                 color: white;
#                 background: #4caf50;
#                 border: none;
#                 border-radius: 4px;
#                 padding: 12px 24px;
#                 margin-right: 5px;
#             }
#             QPushButton:hover { background: #388e3c; }
#             QPushButton:pressed { background: #2e7d32; }
#             QPushButton:disabled { background: #bdbdbd; color: #ffffff; }
#         """
#         )
#         self.start_btn.setEnabled(False)
#         self.start_btn.clicked.connect(self.toggle_detection)

#         reset_btn = QPushButton("Reset")
#         reset_btn.setCursor(Qt.PointingHandCursor)
#         reset_btn.setFixedHeight(48)
#         reset_btn.setStyleSheet(
#             """
#             QPushButton {
#                 font-size: 14px;
#                 font-weight: 500;
#                 color: #757575;
#                 background-color: #ffffff;
#                 border: 1px solid #e0e0e0;
#                 border-radius: 4px;
#                 padding: 12px 24px;
#                 margin-left: 5px;
#             }
#             QPushButton:hover { background-color: #f5f5f5; border: 1px solid #bdbdbd; color: #424242; }
#             QPushButton:pressed { background-color: #eeeeee; }
#         """
#         )
#         button_layout.addWidget(self.start_btn, 2)
#         button_layout.addWidget(reset_btn, 1)
#         left_layout.addLayout(button_layout)

#         self.content_layout.addWidget(self.left_panel)

#         self.right_panel = ModernCard()
#         self.right_panel.setStyleSheet(
#             """
#             QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
#         """
#         )
#         self.right_panel.setVisible(False)
#         right_layout = QVBoxLayout(self.right_panel)
#         right_layout.setContentsMargins(16, 16, 16, 16)
#         right_layout.setSpacing(14)

#         top_row = QHBoxLayout()
#         title_col = QVBoxLayout()
#         title_lbl = QLabel("Offline Attendance")
#         title_lbl.setStyleSheet(
#             """
#             font-size: 20px;
#             font-weight: 700;
#             color: #212121;
#             background: transparent;
#             border: none;
#         """
#         )
#         subtitle_lbl = QLabel("Overview")
#         subtitle_lbl.setStyleSheet(
#             """
#             font-size: 12px;
#             font-weight: 350;
#             color: #212121;
#             background: transparent;
#             border: none;
#         """
#         )
#         title_col.addWidget(title_lbl)
#         title_col.addWidget(subtitle_lbl)
#         top_row.addLayout(title_col)
#         top_row.addStretch()

#         dt_row = QHBoxLayout()
#         dt_row.setSpacing(8)
#         dt_row.setContentsMargins(0, 0, 0, 0)
#         self.date_label = QLabel("Date: --- --- --")
#         self.date_label.setStyleSheet(
#             """
#             font-size: 16px;
#             font-weight: 500;
#             color: #1565c0;
#             background: transparent;
#             border: none;
#         """
#         )
#         self.time_label = QLabel("--:--:--")
#         self.time_label.setStyleSheet(
#             """
#             font-size: 16px;
#             font-weight: 500;
#             color: #1565c0;
#             background: transparent;
#             border: none;
#         """
#         )
#         dt_row.addWidget(self.date_label, 0, Qt.AlignRight)
#         dt_row.addWidget(self.time_label, 0, Qt.AlignRight)
#         top_row.addLayout(dt_row)
#         right_layout.addLayout(top_row)

#         self.overview_grid = QGridLayout()
#         self.overview_grid.setHorizontalSpacing(12)
#         self.overview_grid.setVerticalSpacing(12)
#         self.create_overview_cards()
#         right_layout.addLayout(self.overview_grid)

#         section1_header = QHBoxLayout()
#         title_alert_layout = QHBoxLayout()
#         title_alert_layout.setSpacing(12)
#         s1_title = QLabel("Daily Attendance Log")
#         s1_title.setStyleSheet(
#             """
#             font-size: 20px;
#             font-weight: 700;
#             color: #212121;
#             background: transparent;
#             border: none;
#         """
#         )
#         title_alert_layout.addWidget(s1_title)
#         alert_container = QWidget()
#         alert_layout = QHBoxLayout(alert_container)
#         alert_layout.setContentsMargins(0, 0, 0, 0)
#         alert_layout.setSpacing(6)
#         alert_icon = QLabel("⚠️")
#         alert_icon.setStyleSheet(
#             """
#             QLabel {
#                 font-size: 18px;
#                 color: #FF8C00;
#                 background: transparent;
#                 border: none;
#                 padding: 0px;
#             }
#         """
#         )
#         pending_sync_count = self.get_pending_sync_count()
#         self.alert_msg = QLabel(f"{pending_sync_count} records pending sync")
#         self.alert_msg.setStyleSheet(
#             """
#             QLabel {
#                 font-size: 12px;
#                 color: #FF8C00;
#                 background: transparent;
#                 border: none;
#                 padding: 0px;
#                 font-weight: 500;
#             }
#         """
#         )
#         alert_layout.addWidget(alert_icon)
#         alert_layout.addWidget(self.alert_msg)
#         title_alert_layout.addWidget(alert_container)
#         section1_header.addLayout(title_alert_layout)
#         section1_header.addStretch()

#         search_container = QWidget()
#         search_container.setFixedWidth(220)
#         search_container.setStyleSheet(
#             """
#             QWidget {
#                 border: 1px solid #e0e0e0;
#                 border-radius: 6px;
#                 background: #ffffff;
#             }
#             QWidget:focus-within {
#                 border-color: #bdbdbd;
#             }
#         """
#         )
#         search_layout = QHBoxLayout(search_container)
#         search_layout.setContentsMargins(10, 0, 8, 0)
#         search_layout.setSpacing(6)
#         self.search_input = QLineEdit()
#         self.search_input.setPlaceholderText("Search employee...")
#         self.search_input.setStyleSheet(
#             """
#             QLineEdit {
#                 border: none;
#                 background: transparent;
#                 font-size: 13px;
#                 padding: 8px 0px;
#                 color: #000000;
#             }
#             QLineEdit:focus {
#                 border: none;
#                 outline: none;
#                 color: #000000;
#             }
#         """
#         )
#         search_icon = QLabel("🔍")
#         search_icon.setStyleSheet(
#             """
#             QLabel {
#                 font-size: 14px;
#                 color: #9e9e9e;
#                 background: transparent;
#                 border: none;
#             }
#         """
#         )
#         self.search_input.textChanged.connect(self.search_table)
#         search_layout.addWidget(self.search_input)
#         search_layout.addWidget(search_icon)
#         section1_header.addWidget(search_container)
#         right_layout.addLayout(section1_header)

#         self.daily_table = QTableWidget()
#         self.daily_table.setColumnCount(8)
#         self.daily_table.setHorizontalHeaderLabels(
#             [
#                 "Date",
#                 "Emp Code",
#                 "Name",
#                 "Check-in",
#                 "Check-out",
#                 "Status",
#                 "Mode",
#                 "Sync",
#             ]
#         )
#         header = self.daily_table.horizontalHeader()
#         header.setSectionResizeMode(QHeaderView.ResizeToContents)
#         header.setSectionResizeMode(2, QHeaderView.Stretch)
#         header.setDefaultAlignment(Qt.AlignLeft)
#         self.daily_table.setAlternatingRowColors(True)
#         self.daily_table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.daily_table.verticalHeader().setVisible(False)
#         self.daily_table.setSortingEnabled(True)
#         self.daily_table.setAlternatingRowColors(True)
#         self.daily_table.setStyleSheet(
#             """
#             QTableWidget {
#                 background-color: #ffffff;
#                 alternate-background-color: #d2e7f9; /* Light blue */
#                 border: 1px solid #e0e0e0;
#                 border-radius: 8px;
#                 font-size: 14px;
#                 color: #424242;
#                 gridline-color: #eeeeee;
#                 selection-background-color: #e3f2fd;
#             }
#             QTableWidget::item {
#                 padding: 12px 16px;
#                 border-bottom: 1px solid #eeeeee;
#                 border-right: none;
#             }
#             QTableWidget::item:selected {
#                 background-color: #e3f2fd;
#                 color: #0d47a1;
#                 font-weight: 500;
#             }
#             QHeaderView::section {
#                 background: #001F3F;
#                 color: #ffffff;
#                 font-weight: 500;
#                 font-size: 13px;
#                 padding: 12px 16px;
#                 border: none;
#                 text-transform: uppercase;
#             }
#             QScrollBar:vertical {
#                 background-color: #001F3F;
#                 width: 10px;
#                 border-radius: 4px;
#             }
#             QScrollBar::handle:vertical {
#                 background-color: #bdbdbd;
#                 border-radius: 4px;
#                 min-height: 20px;
#             }
#             QScrollBar::handle:vertical:hover {
#                 background-color: #9e9e9e;
#             }
#             QScrollBar::add-line:vertical {
#                 background: #001F3F;
#                 height: 15px;
#                 border-radius: 4px;
#                 subcontrol-position: bottom;
#                 subcontrol-origin: margin;
#             }
#             QScrollBar::sub-line:vertical {
#                 background: #001F3F;
#                 height: 15px;
#                 border-radius: 4px;
#                 subcontrol-position: top;
#                 subcontrol-origin: margin;
#             }
#             QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {
#                 background: #303f9f;
#             }
#             QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed {
#                 background: #1a237e;
#             }
#             QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
#                 width: 5px;
#                 height: 5px;
#                 background: white;
#             }
#             QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
#                 background: none;
#             }
#             """
#         )

#         self.daily_table.setMinimumHeight(500)
#         self.daily_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         right_layout.addWidget(self.daily_table)
#         right_layout.addItem(
#             QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
#         )

#         self.content_layout.addWidget(self.right_panel, 2)
#         self.main_content_layout.addLayout(self.content_layout)
#         main_layout.addWidget(content_widget, 1)
#         self.load_attendance_logs()

#     def search_table(self, text):
#         text = text.strip().lower()
#         for row in range(self.daily_table.rowCount()):
#             match = False
#             for col in range(self.daily_table.columnCount()):
#                 item = self.daily_table.item(row, col)
#                 if item and text in item.text().lower():
#                     match = True
#                     break
#             self.daily_table.setRowHidden(row, not match)

#     def init_timers(self):
#         try:
#             self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#             if not self.cap.isOpened():
#                 raise Exception("Failed to open camera")
#         except Exception as e:
#             print("Camera unavailable")
#             self.start_btn.setEnabled(False)
#             QMessageBox.critical(self, "Error", f"Failed to initialize camera: {e}")
#             self.cap = None
#             return
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_frame)
#         self.timer.start(30)
#         self.detect_timer = QTimer()
#         self.detect_timer.timeout.connect(self.detect)
#         self.clock_timer = QTimer()
#         self.clock_timer.timeout.connect(self.update_time)
#         self.clock_timer.start(1000)
#         self.data_refresh_timer = QTimer()
#         self.data_refresh_timer.timeout.connect(self.refresh_data)
#         self.is_detecting = False
#         self.update_time()

#     def update_time(self):
#         now = datetime.datetime.now()
#         self.time_label.setText(now.strftime("%I:%M:%S"))
#         self.date_label.setText(f"Date: {now.strftime('%d-%m-%y')}")

#     def update_frame(self):
#         if self.cap is None or not self.cap.isOpened():
#             print("Camera unavailable")
#             self.video_label.setText("No Camera")
#             return
#         try:
#             ret, frame = self.cap.read()
#             if not ret or frame is None or frame.size == 0:
#                 print("Failed to capture frame")
#                 self.video_label.setText("No Frame")
#                 return
#             rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             h, w, ch = rgb.shape
#             qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
#             pixmap = QPixmap.fromImage(qt_image)
#             pixmap = pixmap.scaled(
#                 self.video_label.width(), self.video_label.height(),
#                 Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
#             )
#             self.video_label.setPixmap(pixmap)
#             self.video_label.setText("")
#         except Exception as e:
#             print("Frame update error")
#             self.video_label.setText("Error")

#     def toggle_detection(self):
#         if not self.liveness_detector_loaded:
#             QMessageBox.warning(
#                 self,
#                 "Warning",
#                 "Liveness detector is not loaded yet. Please wait for it to load.",
#             )
#             return
#         if self.cap is None or not self.cap.isOpened():
#             QMessageBox.warning(
#                 self,
#                 "Warning",
#                 "Camera is not available. Please check the camera connection.",
#             )
#             return
#         if self.is_detecting:
#             self.detect_timer.stop()
#             self.start_btn.setText("Start Detection")
#             self.start_btn.setStyleSheet(
#                 """
#                 QPushButton { font-size: 14px; font-weight: 500; color: white; background: #4caf50; border: none; border-radius: 4px; padding: 12px 24px; }
#                 QPushButton:hover { background: #388e3c; }
#             """
#             )
#             print("Detection stopped")
#         else:
#             self.detect_timer.start(1000)
#             self.start_btn.setText("Stop Detection")
#             self.start_btn.setStyleSheet(
#                 """
#                 QPushButton { font-size: 14px; font-weight: 500; color: white; background: #f44336; border: none; border-radius: 4px; padding: 12px 24px; }
#                 QPushButton:hover { background: #d32f2f; }
#             """
#             )
#         self.is_detecting = not self.is_detecting

#     def detect(self):
#         if not self.liveness_detector_loaded or self.detect_and_predict is None:
#             return
#         if self.cap is None or not self.cap.isOpened():
#             return
#         if getattr(self, "detect_worker_running", False):
#             return
#         ret, frame = self.cap.read()
#         if not ret or frame is None or frame.size == 0:
#             return
#         if len(frame.shape) != 3 or frame.shape[2] != 3:
#             frame = (
#                 cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
#                 if len(frame.shape) == 2
#                 else frame
#             )
#         self.detect_worker_running = True
#         self._detect_worker = DetectWorker(self.detect_and_predict, frame)
#         self._detect_worker.result_ready.connect(self.on_detect_result)
#         self._detect_worker.finished.connect(
#             lambda: setattr(self, "detect_worker_running", False)
#         )
#         self._detect_worker.start()

#     def on_detect_result(self, result):
#         try:
#             if result.get("status"):
#                 if is_logged_in():
#                     self.load_attendance_logs()
#                 name = result.get("emp_full_name", "Employee")
#                 self.employee_card.update_value(name)
#                 self.update_camera_border("recognized")
#                 self.reset_camera_border_after_delay()
#                 speak("Hello " + name)
#                 if is_logged_in():
#                     self.daily_table.scrollToTop()
#             else:
#                 name = result.get("emp_full_name", "Unknown")
#                 self.employee_card.update_value(name)
#                 msg = result.get("message", "")
#                 if msg and "detect" in msg.lower():
#                     self.update_camera_border("detecting")
#                 else:
#                     self.update_camera_border("failed")
#                     self.reset_camera_border_after_delay()
#         except Exception:
#             pass

#     def resume_detection(self):
#         if self.is_detecting:
#             print("Scanning for faces...")
#             self.detect_timer.start(1000)

#     def load_attendance_logs(self):
#         if not is_logged_in():
#             return
#         logs = get_attendance_logs()
#         current_scroll_pos = self.daily_table.verticalScrollBar().value()
#         selected_rows = [index.row() for index in self.daily_table.selectionModel().selectedRows()]
#         self.daily_table.setRowCount(0)
#         if hasattr(self, "date_label"):
#             self.date_label.setText(
#                 f"Date: {datetime.datetime.now().strftime('%d-%m-%y')}"
#             )
#         for log in logs:
#             row_pos = self.daily_table.rowCount()
#             self.daily_table.insertRow(row_pos)
#             # sync_status = is_record_synced(log["emp_code"], log["checkin_date"])
#             row_data = [
#                 format_date_ddmmyy(log["checkin_date"]),
#                 str(log["emp_code"]),
#                 log["emp_full_name"],
#                 log["checkin_time"],
#                 log["checkout_time"] if log["checkout_time"] else "-",
#                 log["status"] if log["status"] else "Pending",
#                 log.get("mode", "Offline-Face"),
#                 "Synced" if log.get("sync", 0) == 1 else "Not Synced",
#             ]
#             for col, text in enumerate(row_data):
#                 item = QTableWidgetItem(text)
#                 if col == 5:
#                     if text == "CHECKED_IN":
#                         item = QTableWidgetItem("MSP")
#                         item.setForeground(QColor("orange"))
#                     elif text == "CHECKED_OUT":
#                         item = QTableWidgetItem("Present")
#                         item.setForeground(QColor("green"))
#                     else:
#                         item.setForeground(QColor("blue"))
#                 item.setFont(QFont("Segoe UI", 10, QFont.Bold))
#                 self.daily_table.setItem(row_pos, col, item)
#         self.daily_table.verticalScrollBar().setValue(current_scroll_pos)
#         if selected_rows:
#             for row in selected_rows:
#                 if row < self.daily_table.rowCount():
#                     self.daily_table.selectRow(row)

#     def update_table_by_date(self, selected_date):
#         if not is_logged_in():
#             return
#         logs = get_attendance_by_date(selected_date)
#         current_scroll_pos = self.daily_table.verticalScrollBar().value()
#         selected_rows = [index.row() for index in self.daily_table.selectionModel().selectedRows()]
#         if hasattr(self, "date_label"):
#             self.date_label.setText(
#                 f"Date: {format_date_ddmmyy(selected_date)}"
#             )
#         self.daily_table.setRowCount(0)
#         if logs:
#             for log in logs:
#                 row_pos = self.daily_table.rowCount()
#                 self.daily_table.insertRow(row_pos)
#                 row_data = [
#                     format_date_ddmmyy(log["checkin_date"]),
#                     str(log["emp_code"]),
#                     log["emp_full_name"],
#                     log["checkin_time"],
#                     log["checkout_time"] if log["checkout_time"] else "-",
#                     log["status"] if log["status"] else "Pending",
#                     log.get("mode", "Offline-Face"),
#                     "Synced" if log.get("sync", 0) == 1 else "Not Synced",
#                 ]
#                 for col, text in enumerate(row_data):
#                     item = QTableWidgetItem(text)
#                     if col == 5:
#                         if text == "CHECKED_IN":
#                             item = QTableWidgetItem("MSP")
#                             item.setForeground(QColor("orange"))
#                         elif text == "CHECKED_OUT":
#                             item = QTableWidgetItem("Present")
#                             item.setForeground(QColor("green"))
#                         else:
#                             item.setForeground(QColor("blue"))
#                     item.setFont(QFont("Segoe UI", 10, QFont.Bold))
#                     self.daily_table.setItem(row_pos, col, item)
#         self.daily_table.verticalScrollBar().setValue(current_scroll_pos)
#         if selected_rows:
#             for row in selected_rows:
#                 if row < self.daily_table.rowCount():
#                     self.daily_table.selectRow(row)
#         else:
#             print(f"No attendance found for {selected_date}")

# def run_app():
#     app = QApplication(sys.argv)
#     init_db()
#     session = load_session() if is_logged_in() else {"name": "Guest"}
#     window = AttendanceApp(session)
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     run_app()



import os
import sys
import cv2
import datetime
import importlib.metadata
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QCalendarWidget,
    QScrollArea,
    QToolButton,
    QStyle,
    QStyledItemDelegate,
    QTableView,
    QGraphicsDropShadowEffect,
    QDesktopWidget,
    QCheckBox,
    QTimeEdit,
    QDateEdit,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QLCDNumber,
)
from PyQt5.QtCore import (
    QTimer,
    Qt,
    pyqtSignal,
    QThread,
    QSize,
    QDate,
    QTime,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    QRect,
)
from PyQt5.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPainterPath,
    QColor,
    QFont,
    QPen,
    QBrush,
    QIcon,
    QRegion,
    QCursor, 
    QPalette,
    QResizeEvent,
)
from recognition import warm_up_recognition, build_index_now

# Enable high DPI scaling before any QApplication is created
try:
    from PyQt5 import QtCore
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    pass
from fetch_emp_from_fixhr import fetch_and_store_employees
from login import login_fixhr, is_logged_in, load_session, clear_session
from database import (
    get_attendance_logs,
    get_daily_attendance_summary,
    get_employee_count,
    get_attendance_by_date,
    init_db,
    start_background_sync,
    get_sync_status_overview,
    get_remaining_sync_count,
    get_sync_settings,
    set_setting,
    get_setting,
    get_failed_sync_records,
    sync_data_to_server,
    retry_failed_sync,
)
from device_info import get_device_info, is_internet_available
from speak import speak
from backup_utils import BackupManager
import io

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(open(os.devnull, 'w').detach(), encoding="utf-8")

def format_date_ddmmyy(date_str: str) -> str:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d-%m-%y")
    except Exception:
        try:
            dt = datetime.datetime.strptime(date_str, "%Y/%m/%d")
            return dt.strftime("%d-%m-%y")
        except Exception:
            return date_str

class FetchThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, token):
        super().__init__()
        self.token = token

    def run(self):
        try:
            fetch_and_store_employees(self.token)
            self.finished.emit(True, "Employees fetched successfully")
        except Exception as e:
            self.finished.emit(False, str(e))

class LivenessLoaderThread(QThread):
    finished = pyqtSignal(bool, str, object)

    def run(self):
        try:
            from liveness_detector import detect_and_predict
            self.finished.emit(
                True, "Liveness detector loaded successfully", detect_and_predict
            )
        except ImportError as e:
            self.finished.emit(False, f"Failed to load liveness detector: {e}", None)
        except Exception as e:
            self.finished.emit(False, f"Unexpected error loading detector: {e}", None)

class ProfileWarmupThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            info = warm_up_recognition()
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))

class BuildIndexThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            info = build_index_now()
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class ManualSyncThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, sync_mode="both", start_date=None, end_date=None):
        super().__init__()
        self.sync_mode = sync_mode
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            result = sync_data_to_server(
                sync_mode=self.sync_mode,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        except Exception as exc:
            result = {"success": False, "message": str(exc)}
        self.finished.emit(result)


class BackgroundSyncThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, sync_mode=None, start_date=None, end_date=None):
        super().__init__()
        self.sync_mode = sync_mode
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            result = sync_data_to_server(
                sync_mode=self.sync_mode,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        except Exception as exc:
            result = {"success": False, "message": str(exc), "records_synced": 0, "records_failed": 0}
        self.finished.emit(result)


class FailedRetryThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, record_ids=None):
        super().__init__()
        self.record_ids = record_ids

    def run(self):
        try:
            result = retry_failed_sync(self.record_ids)
        except Exception as exc:
            result = {"success": False, "message": str(exc)}
        self.finished.emit(result)

class ModalLoader(QDialog):
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(360, 160)
        self.setStyleSheet("""
            QDialog { background-color: #001F3F; color: #ffffff; }
            QLabel { color: #ffffff; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.header = QLabel(title)
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.body = QLabel(message)
        self.body.setAlignment(Qt.AlignCenter)
        self.body.setWordWrap(True)
        self.body.setStyleSheet("font-size: 12px; color: #d0d0d0;")

        self.hint = QLabel("Please wait...")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("font-size: 11px; color: #9aa7b2;")

        layout.addWidget(self.header)
        layout.addStretch(1)
        layout.addWidget(self.body)
        layout.addWidget(self.hint)
        layout.addStretch(1)

        # Center on screen
        geo = QDesktopWidget().availableGeometry(self)
        self.move(geo.center() - self.rect().center())


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)
    sync_completed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sync Settings")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.current_settings = get_sync_settings()
        self.sync_thread = None
        self.failed_retry_thread = None

        self.setStyleSheet(
            """
            QDialog {
                background-color: #0f1c2e;
                color: #e8edf2;
            }
            QGroupBox {
                border: 1px solid #1f3b59;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px 12px;
                font-weight: 600;
                color: #8fdcfe;
            }
            QLabel { color: #e8edf2; }
            QCheckBox, QRadioButton { color: #e8edf2; }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 4px;
                padding: 8px 18px;
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton:disabled {
                background-color: #3a4a60;
                color: #9aa7b2;
            }
            QTimeEdit, QDateEdit {
                background-color: #12233a;
                border: 1px solid #1f3b59;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self.auto_group = self._build_auto_sync_group()
        main_layout.addWidget(self.auto_group)

        self.mode_group_box = self._build_mode_group()
        main_layout.addWidget(self.mode_group_box)

        self.date_group = self._build_date_range_group()
        main_layout.addWidget(self.date_group)

        self.failed_group = self._build_failed_queue_group()
        main_layout.addWidget(self.failed_group)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.handle_save)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.close_btn)
        main_layout.addLayout(button_row)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_live_clock)
        self.clock_timer.start(1000)
        self.update_auto_sync_ui(self.auto_sync_checkbox.isChecked())
        self.update_live_clock()

    def _build_auto_sync_group(self):
        group = QGroupBox("Automatic Sync Scheduler")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self.auto_sync_checkbox = QCheckBox("Enable automatic daily sync")
        self.auto_sync_checkbox.setChecked(self.current_settings["auto_sync_enabled"])
        self.auto_sync_checkbox.toggled.connect(self.update_auto_sync_ui)
        layout.addWidget(self.auto_sync_checkbox)

        self.schedule_frame = QFrame()
        schedule_layout = QHBoxLayout(self.schedule_frame)
        schedule_layout.setContentsMargins(0, 0, 0, 0)
        schedule_layout.setSpacing(12)

        time_col = QVBoxLayout()
        time_label = QLabel("Run every day at:")
        time_label.setStyleSheet("color: #9aa7b2;")
        time_col.addWidget(time_label)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        time_text = self.current_settings["auto_sync_time"]
        try:
            hours, minutes = map(int, time_text.split(":"))
        except ValueError:
            hours, minutes = (9, 0)
        self.time_edit.setTime(QTime(hours, minutes))
        self.time_edit.setStyleSheet("font-size: 16px;")
        time_col.addWidget(self.time_edit)
        schedule_layout.addLayout(time_col)

        clock_col = QVBoxLayout()
        clock_label = QLabel("Current time")
        clock_label.setStyleSheet("color: #9aa7b2;")
        clock_col.addWidget(clock_label)

        self.clock_display = QLCDNumber()
        self.clock_display.setDigitCount(5)
        self.clock_display.setSegmentStyle(QLCDNumber.Flat)
        self.clock_display.setStyleSheet(
            """
            QLCDNumber {
                background-color: #12233a;
                border: 1px solid #1f3b59;
                border-radius: 4px;
            }
            """
        )
        clock_col.addWidget(self.clock_display)
        schedule_layout.addLayout(clock_col)

        layout.addWidget(self.schedule_frame)
        return group

    def _build_mode_group(self):
        group = QGroupBox("Sync Mechanism")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.mode_button_group = QButtonGroup(self)
        modes = [
            ("both", "Sync both check-in and check-out data"),
            ("checkin", "Sync only check-in punches"),
            # ("checkout", "Sync only check-out punches"),
        ]
        self.mode_buttons = {}

        for key, label in modes:
            btn = QRadioButton(label)
            btn.setProperty("mode_key", key)
            self.mode_button_group.addButton(btn)
            self.mode_buttons[key] = btn
            layout.addWidget(btn)

        active_mode = self.current_settings["sync_mode"]
        if active_mode not in self.mode_buttons:
            active_mode = "both"
        self.mode_buttons[active_mode].setChecked(True)
        return group

    def _build_date_range_group(self):
        group = QGroupBox("Sync Historical Date Range")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        picker_row = QHBoxLayout()
        picker_row.setSpacing(10)

        start_col = QVBoxLayout()
        start_label = QLabel("Start date")
        start_label.setStyleSheet("color: #9aa7b2;")
        start_col.addWidget(start_label)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.start_date_edit.setDate(QDate.currentDate().addDays(-1))
        start_col.addWidget(self.start_date_edit)
        picker_row.addLayout(start_col)

        end_col = QVBoxLayout()
        end_label = QLabel("End date")
        end_label.setStyleSheet("color: #9aa7b2;")
        end_col.addWidget(end_label)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.end_date_edit.setDate(QDate.currentDate())
        end_col.addWidget(self.end_date_edit)
        picker_row.addLayout(end_col)

        layout.addLayout(picker_row)

        self.date_range_sync_btn = QPushButton("Sync Selected Range")
        self.date_range_sync_btn.clicked.connect(self.handle_range_sync)
        layout.addWidget(self.date_range_sync_btn, alignment=Qt.AlignLeft)

        self.date_range_status = QLabel("")
        self.date_range_status.setWordWrap(True)
        self.date_range_status.setStyleSheet("color: #9aa7b2; font-size: 11px;")
        layout.addWidget(self.date_range_status)

        return group

    def _build_failed_queue_group(self):
        group = QGroupBox("Failed Sync Queue")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self.failed_queue_table = QTableWidget()
        self.failed_queue_table.setColumnCount(6)
        self.failed_queue_table.setHorizontalHeaderLabels(
            ["Emp Code", "Date", "Time", "Attempts", "Last Attempt", "Error"]
        )
        self.failed_queue_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.failed_queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.failed_queue_table.setSelectionMode(QTableWidget.MultiSelection)
        
        # Fix text color for headers and data
        self.failed_queue_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #212121;
                gridline-color: #e0e0e0;
                font-size: 11px;
            }
            QTableWidget::item {
                color: #212121;
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #212121;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout.addWidget(self.failed_queue_table)

        btn_row = QHBoxLayout()
        self.retry_failed_btn = QPushButton("Retry Selected")
        self.retry_failed_btn.clicked.connect(self.handle_retry_failed)
        self.refresh_failed_btn = QPushButton("Refresh")
        self.refresh_failed_btn.clicked.connect(self.load_failed_queue)
        btn_row.addWidget(self.retry_failed_btn)
        btn_row.addWidget(self.refresh_failed_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.failed_status = QLabel("")
        self.failed_status.setStyleSheet("color: #9aa7b2; font-size: 11px;")
        layout.addWidget(self.failed_status)

        self.load_failed_queue()
        return group

    def update_auto_sync_ui(self, checked):
        self.schedule_frame.setVisible(bool(checked))

    def update_live_clock(self):
        now = datetime.datetime.now()
        self.clock_display.display(now.strftime("%H:%M"))

    def get_selected_mode(self):
        button = self.mode_button_group.checkedButton()
        if button:
            return button.property("mode_key")
        return "both"

    def handle_save(self):
        auto_enabled = "1" if self.auto_sync_checkbox.isChecked() else "0"
        auto_time = self.time_edit.time().toString("HH:mm")
        selected_mode = self.get_selected_mode()

        set_setting("auto_sync_enabled", auto_enabled)
        set_setting("auto_sync_time", auto_time)
        set_setting("sync_mode", selected_mode)
        set_setting("auto_sync_last_run", "")

        updated = get_sync_settings()
        self.current_settings = updated
        self.settings_saved.emit(updated)
        QMessageBox.information(self, "Settings Saved", "Sync preferences updated successfully.")

    def handle_range_sync(self):
        if self.sync_thread and self.sync_thread.isRunning():
            QMessageBox.information(self, "Sync Running", "Please wait for the current sync to finish.")
            return

        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Range", "Start date must be before end date.")
            return

        start_str = start_date.toString("dd-MM-yyyy")
        end_str = end_date.toString("dd-MM-yyyy")
        mode = self.get_selected_mode()

        self.date_range_sync_btn.setEnabled(False)
        self.date_range_status.setText(
            f"Syncing logs from {start_str} to {end_str} ({mode}) ..."
        )

        self.sync_thread = ManualSyncThread(sync_mode=mode, start_date=start_str, end_date=end_str)
        self.sync_thread.finished.connect(self.on_range_sync_finished)
        self.sync_thread.start()

    def on_range_sync_finished(self, result):
        self.date_range_sync_btn.setEnabled(True)
        self.sync_thread = None
        self.date_range_status.setText(result.get("message", "Sync finished"))
        
        # Show detailed sync completion popup
        records_synced = result.get("records_synced", 0)
        records_failed = result.get("records_failed", 0)
        
        if result.get("success"):
            message = f"Sync Completed Successfully!\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Sync completed successfully.")
            QMessageBox.information(self, "Sync Complete", message)
        else:
            message = f"Sync Completed with Issues\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Sync failed. Please check logs.")
            QMessageBox.warning(self, "Sync Issue", message)
        
        self.sync_completed.emit(result)
        self.load_failed_queue()

    def load_failed_queue(self):
        if not hasattr(self, "failed_queue_table"):
            return
        records = get_failed_sync_records()
        self.failed_queue_table.setRowCount(0)
        for row_idx, rec in enumerate(records):
            self.failed_queue_table.insertRow(row_idx)
            for col, value in enumerate(
                [
                    rec["emp_code"],
                    rec["checkin_date"],
                    rec["checkin_time"],
                    str(rec["attempts"]),
                    rec["last_attempt_at"] or "-",
                    rec["error_message"] or "-",
                ]
            ):
                item = QTableWidgetItem(value)
                item.setForeground(QColor("#212121"))  # Set text color to dark
                if col == 5:
                    item.setToolTip(value)
                item.setData(Qt.UserRole, rec["id"])
                self.failed_queue_table.setItem(row_idx, col, item)
        self.failed_status.setText(f"{len(records)} failed record(s) in queue.")

    def handle_retry_failed(self):
        if self.failed_retry_thread and self.failed_retry_thread.isRunning():
            QMessageBox.information(self, "Retry Running", "A retry job is already running.")
            return
        selected = self.failed_queue_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Select Records", "Please select at least one row to retry.")
            return
        record_ids = []
        for idx in selected:
            item = self.failed_queue_table.item(idx.row(), 0)
            if item:
                record_ids.append(item.data(Qt.UserRole))
        self.retry_failed_btn.setEnabled(False)
        self.failed_status.setText("Retrying selected failed records...")
        self.failed_retry_thread = FailedRetryThread(record_ids)
        self.failed_retry_thread.finished.connect(self.on_retry_finished)
        self.failed_retry_thread.start()

    def on_retry_finished(self, result):
        self.retry_failed_btn.setEnabled(True)
        self.failed_retry_thread = None
        self.failed_status.setText(result.get("message", "Retry finished"))
        if result.get("success"):
            QMessageBox.information(self, "Retry Complete", result.get("message", "Retry completed successfully."))
        else:
            QMessageBox.warning(self, "Retry Issue", result.get("message", "Retry failed."))
        self.load_failed_queue()
        self.sync_completed.emit(result)

class DetectWorker(QThread):
    result_ready = pyqtSignal(dict)

    def __init__(self, detector_fn, frame):
        super().__init__()
        self.detector_fn = detector_fn
        self.frame = frame

    def run(self):
        try:
            result = self.detector_fn(self.frame)
        except Exception as e:
            result = {
                "status": False,
                "emp_full_name": "System Error",
                "message": str(e),
            }
        self.result_ready.emit(result)

class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #001F3F;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 0px;
            }
        """
        )

class StatusCard(QFrame):
    def __init__(self, title, value, color="#6d200d", parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet(
            f"""
            QFrame {{
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            font-size: 12px; font-weight: 500; color: #757575; background: transparent;
        """
        )
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Value label
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            """
            font-size: 14px; font-weight: 600; color: #212121; background: transparent;
        """
        )
        self.value_label.setWordWrap(True)
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def update_value(self, value):
        self.value_label.setText(value)

class SidebarButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(35)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(self.get_default_style())

    def get_default_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
                color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #E3F2FD;
            }
        """

    def set_active(self, active=True):
        if active:
            self.setStyleSheet(
                """
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: none;
                    border-radius: 6px;
                    background-color: #E3F2FD;
                    color: #1976d2;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #E3F2FD; }
            """
            )
        else:
            self.setStyleSheet(self.get_default_style())

class CalendarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        date = index.data()
        if not date:
            return

        rect = option.rect
        text = str(date)
        today = QDate.currentDate().day()
        is_today = text.isdigit() and int(text) == today
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        painter.save()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 4
        accent = QColor("#0078D7")

        if is_today and not is_selected:
            painter.setBrush(QBrush(accent))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        elif is_selected:
            painter.setBrush(QBrush(accent.lighter(150)))
            painter.setPen(QPen(accent, 2))
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        elif is_hovered:
            painter.setBrush(QBrush(QColor(0, 120, 215, 60)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        else:
            painter.setPen(QPen(QColor(50, 50, 50)))
            painter.setBrush(Qt.NoBrush)

        painter.setFont(option.font)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

def get_app_version():
    try:
        return importlib.metadata.version("FixHR")
    except importlib.metadata.PackageNotFoundError:
        return "1.0.0"

class Sidebar(QFrame):
    dashboard_clicked = pyqtSignal()
    attendance_clicked = pyqtSignal()
    employees_clicked = pyqtSignal()
    reports_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    date_selected = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.expanded_width = 280
        self.collapsed_width = 60
        self.is_collapsed = False
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.expanded_width)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #001F3F;
            }
        """
        )
        self.active_button = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(8, 5, 8, 5)
        top_bar_layout.setSpacing(0)

        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(2)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignLeft)

        try:
            pixmap = QPixmap(resource_path("logo_dark.png"))
            pixmap = pixmap.scaled(100, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
            self.logo_label.setFixedSize(pixmap.width(), pixmap.height())
        except:
            self.logo_label.setText("FixHR")
            self.logo_label.setStyleSheet(
                "font-size: 16px; font-weight: 700; color: #FF8C00; background: transparent;"
            )
        
        self.logo_label.setStyleSheet("background: transparent;")

        self.version_label = QLabel(f"v{get_app_version()}")
        self.version_label.setStyleSheet(
            "font-size: 10px; color: #ffffff; background: transparent;"
        )
        self.version_label.setAlignment(Qt.AlignLeft)

        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.version_label)
        top_bar_layout.addWidget(logo_frame, alignment=Qt.AlignLeft)

        top_bar_layout.addStretch()

        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.toggle_btn.setIconSize(QSize(20, 20))
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(
            """
            QToolButton {
                border: none;
                background-color: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 4px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.25);
            }
        """
        )
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        top_bar_layout.addWidget(self.toggle_btn, alignment=Qt.AlignRight)

        main_layout.addWidget(top_bar)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 5, 15)
        layout.setAlignment(Qt.AlignTop)

        user_info_frame = QFrame()
        user_info_frame.setStyleSheet("background: transparent;")
        user_info_layout = QVBoxLayout(user_info_frame)
        user_info_layout.setSpacing(4)
        user_info_layout.setContentsMargins(0, 0, 0, 0)

        user_avatar = QLabel("👤")
        user_avatar.setFixedSize(60, 60)
        user_avatar.setAlignment(Qt.AlignCenter)
        user_avatar.setStyleSheet("""
            font-size: 40px;
            background-color: #002F5E;
            border-radius: 30px;
            padding: 6px;
            color: #F5F5F5;
            border: 2px solid #004080;
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(1)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 120))
        user_avatar.setGraphicsEffect(shadow)

        user_name = QLabel(f"Welcome, {self.session.get('name','User')}")
        user_name.setStyleSheet("font-size: 12px; font-weight: 600; color: #ffffff; background: transparent;")
        user_name.setAlignment(Qt.AlignCenter)
        user_name.setWordWrap(True)

        user_role = QLabel("Admin" if is_logged_in() else "Guest")
        user_role.setStyleSheet("font-size: 10px; color: #cccccc; background: transparent;")
        user_role.setAlignment(Qt.AlignCenter)

        user_info_layout.addWidget(user_avatar, alignment=Qt.AlignCenter)
        user_info_layout.addWidget(user_name, alignment=Qt.AlignCenter)
        user_info_layout.addWidget(user_role, alignment=Qt.AlignCenter)

        layout.addWidget(user_info_frame, alignment=Qt.AlignHCenter)

        layout.addSpacing(15)

        self.nav_label = QLabel("NAVIGATION")
        self.nav_label.setStyleSheet(
            "font-size: 10px; font-weight: 600; color: #9e9e9e; margin-bottom: 8px; background: transparent;"
        )
        layout.addWidget(self.nav_label, alignment=Qt.AlignLeft)

        self.nav_buttons = {}

        if is_logged_in():
            def add_shadow(button):
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(8)
                shadow.setXOffset(1)
                shadow.setYOffset(1)
                shadow.setColor(QColor(0, 0, 0, 100))
                button.setGraphicsEffect(shadow)

            # Horizontal layout for icon buttons
            icon_buttons_layout = QHBoxLayout()
            icon_buttons_layout.setSpacing(8)
            icon_buttons_layout.setContentsMargins(0, 0, 0, 0)

            # Fetch Employees Icon Button
            self.fetch_btn = QToolButton()
            self.fetch_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
            self.fetch_btn.setIconSize(QSize(20, 20))
            self.fetch_btn.setToolTip("Fetch Employees")
            self.fetch_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.fetch_btn.setFixedSize(36, 36)
            self.fetch_btn.setStyleSheet("""
                QToolButton {
                    background-color: #002F5E;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                }
                QToolButton:hover {
                    background-color: #004080;
                }
                QToolButton:pressed {
                    background-color: #001F3F;
                }
            """)
            add_shadow(self.fetch_btn)
            self.fetch_btn.clicked.connect(lambda: self.parent().fetch_employees())
            icon_buttons_layout.addWidget(self.fetch_btn)

            # Sync Attendance Icon Button
            self.sync_btn = QToolButton()
            self.sync_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
            self.sync_btn.setIconSize(QSize(20, 20))
            self.sync_btn.setToolTip("Sync Attendance")
            self.sync_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.sync_btn.setFixedSize(36, 36)
            self.sync_btn.setStyleSheet("""
                QToolButton {
                    background-color: #002F5E;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                }
                QToolButton:hover {
                    background-color: #004080;
                }
                QToolButton:pressed {
                    background-color: #001F3F;
                }
            """)
            add_shadow(self.sync_btn)
            self.sync_btn.clicked.connect(self.start_sync)
            icon_buttons_layout.addWidget(self.sync_btn)

            # # Settings Icon Button
            # self.settings_btn = QToolButton()
            # self.settings_btn.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            # self.settings_btn.setIconSize(QSize(20, 20))
            # self.settings_btn.setToolTip("Settings")
            # self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
            # self.settings_btn.setFixedSize(36, 36)
            # self.settings_btn.setStyleSheet("""
            #     QToolButton {
            #         background-color: #002F5E;
            #         color: white;
            #         border: none;
            #         border-radius: 6px;
            #     }
            #     QToolButton:hover {
            #         background-color: #004080;
            #     }
            #     QToolButton:pressed {
            #         background-color: #001F3F;
            #     }
            # """)
            # add_shadow(self.settings_btn)
            # self.settings_btn.clicked.connect(self.open_settings)
            # icon_buttons_layout.addWidget(self.settings_btn)

            # icon_buttons_layout.addStretch()
            # layout.addLayout(icon_buttons_layout)

           # Settings Icon Button
            self.settings_btn = QToolButton()
            self.settings_btn.setText("⚙")  # Gear icon
            self.settings_btn.setFont(QFont("Segoe UI Symbol", 18))  # Adjust size
            self.settings_btn.setToolTip("Settings")
            self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.settings_btn.setFixedSize(36, 36)
            self.settings_btn.setStyleSheet("""
                QToolButton {
                    background-color: #002F5E;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    qproperty-iconSize: 20px; 
                    padding: 0px;
                }
                QToolButton:hover {
                    background-color: #004080;
                }
                QToolButton:pressed {
                    background-color: #001F3F;
                }
            """)
            add_shadow(self.settings_btn)
            self.settings_btn.clicked.connect(self.open_settings)
            icon_buttons_layout.addWidget(self.settings_btn)

            icon_buttons_layout.addStretch()
            layout.addLayout(icon_buttons_layout)



        layout.addStretch()

        self.cal_label = QLabel("CALENDAR")
        self.cal_label.setStyleSheet(
            "font-size: 10px; font-weight: 600; color: #9e9e9e; margin-bottom: 8px; background: transparent;"
        )
        layout.addWidget(self.cal_label, alignment=Qt.AlignLeft)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.calendar.setMaximumHeight(200)
        self.calendar.setStyleSheet(
            """
            QCalendarWidget {
                background-color: #001F3F;
                border: 1px solid #2c3e50;
                color: white;
                font-size: 10px;
            }
            QCalendarWidget QToolButton {
                color: white;
                font-size: 12px;
                background-color: #002F5E;
                border: none;
                margin: 1px;
                padding: 2px;
            }
            QCalendarWidget QMenu {
                background-color: #001F3F;
                color: white;
                border: 1px solid #2c3e50;
            }
            QCalendarWidget QMenu::item {
                background-color: #001F3F;
                color: white;
                padding: 4px 8px;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #004080;
                color: white;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #001F3F;
                color: white;
            }
        """
        )
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.on_date_selected)

        view = self.calendar.findChild(QTableView)
        if view:
            view.setItemDelegate(CalendarDelegate(view))

        layout.addWidget(self.calendar, alignment=Qt.AlignLeft)

        main_layout.addWidget(scroll)

    def start_sync(self):
        try:
            # Use BackgroundSyncThread to get sync results
            if hasattr(self, "sync_thread") and self.sync_thread and self.sync_thread.isRunning():
                QMessageBox.information(self, "Sync Running", "Sync is already in progress. Please wait.")
                return
            
            self.sync_thread = BackgroundSyncThread()
            self.sync_thread.finished.connect(self.on_sync_finished)
            self.sync_thread.start()
            QMessageBox.information(self, "Sync Started", "Attendance sync started. You will be notified when it completes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start attendance sync: {str(e)}")
    
    def on_sync_finished(self, result):
        """Handle sync completion and show popup with sync/failed counts"""
        records_synced = result.get("records_synced", 0)
        records_failed = result.get("records_failed", 0)
        
        if result.get("success"):
            message = f"Sync Completed Successfully!\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Sync completed successfully.")
            QMessageBox.information(self, "Sync Complete", message)
        else:
            message = f"Sync Completed with Issues\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Sync failed. Please check logs.")
            QMessageBox.warning(self, "Sync Issue", message)
        
        # Refresh data and attendance table if logged in
        if is_logged_in():
            parent = self.parent()
            if parent and hasattr(parent, "refresh_data"):
                parent.refresh_data()
            # Also directly refresh the attendance table to ensure sync status is updated
            if parent and hasattr(parent, "load_attendance_logs"):
                parent.load_attendance_logs()

    def open_settings(self):
        parent = self.parent()
        if parent and hasattr(parent, "open_settings_dialog"):
            parent.open_settings_dialog()

    def on_date_selected(self):
        selected_date = self.calendar.selectedDate().toString("dd-MM-yyyy")
        self.date_selected.emit(selected_date)

    def toggle_sidebar(self):
        if self.is_collapsed:
            self.setFixedWidth(self.expanded_width)
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
            self.logo_label.show()
            self.version_label.show()
            self.nav_label.show()
            if hasattr(self, 'cal_label'):
                self.cal_label.show()
            if hasattr(self, 'calendar'):
                self.calendar.show()
            if hasattr(self, 'fetch_btn'):
                self.fetch_btn.show()
            if hasattr(self, 'sync_btn'):
                self.sync_btn.show()
            if hasattr(self, 'settings_btn'):
                self.settings_btn.show()
            self.is_collapsed = False
        else:
            self.setFixedWidth(self.collapsed_width)
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
            self.logo_label.hide()
            self.version_label.hide()
            self.nav_label.hide()
            if hasattr(self, 'cal_label'):
                self.cal_label.hide()
            if hasattr(self, 'calendar'):
                self.calendar.hide()
            if hasattr(self, 'fetch_btn'):
                self.fetch_btn.hide()
            if hasattr(self, 'sync_btn'):
                self.sync_btn.hide()
            if hasattr(self, 'settings_btn'):
                self.settings_btn.hide()
            self.is_collapsed = True

    def set_active_button(self, button_name):
        if self.active_button:
            self.active_button.set_active(False)
        if button_name in self.nav_buttons:
            self.nav_buttons[button_name].set_active(True)
            self.active_button = self.nav_buttons[button_name]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(600, 450)
        
        # Get screen geometry for responsive sizing
        screen = QDesktopWidget().screenGeometry()
        if screen.width() < 1024:
            self.setFixedSize(400, 350)
        
        bg_img = resource_path("background-img.jpg")
        bg_img = bg_img.replace("\\", "/")
        self.setStyleSheet(
            f"""
            QDialog {{
                background-image: url({bg_img});
                background-position: center;
                background-repeat: no-repeat;
                font-family: 'Segoe UI', sans-serif;
            }}
        """
        )
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 20, 50, 50)
        main_layout.setSpacing(20)
        
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                border-radius: 15px;
            }
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 10, 30, 30)
        container_layout.setSpacing(12)
        
        user_icon = QLabel()
        user_icon.setFixedSize(80, 80)
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
        painter.drawEllipse(5, 5, 70, 70)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(30, 20, 20, 20)
        painter.setPen(QPen(QColor(255, 255, 255), 4))
        painter.drawArc(25, 45, 30, 25, 0, 180 * 16)
        painter.end()
        user_icon.setPixmap(pixmap)
        user_icon.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(user_icon, alignment=Qt.AlignCenter)
        
        title_label = QLabel("FixHr User")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
                padding-bottom: 8px;
            }
        """
        )
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)
        
        username_layout = QVBoxLayout()
        username_label = QLabel("User name:")
        username_label.setStyleSheet(
            "font-size: 14px; color: #FFFFFF; margin-bottom: 4px;"
        )
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                min-width: 200px;
                background-color: transparent;
                color: white;
            }
        """
        )
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        container_layout.addLayout(username_layout)
        
        password_layout = QVBoxLayout()
        password_label = QLabel("Password:")
        password_label.setStyleSheet(
            "font-size: 14px; color: #FFFFFF; margin-bottom: 4px;"
        )
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 14px;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                min-width: 200px;
                background-color: transparent;
                color: white;
            }
        """
        )
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        container_layout.addLayout(password_layout)
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: transparent;
                border: 2px solid #3f51b5;
                border-radius: 8px;
                padding: 12px 24px;
                min-width: 120px;
            }
            QPushButton:hover {
                border: 2px solid #354497;
            }
        """
        )
        login_btn.clicked.connect(self.accept)
        container_layout.addWidget(login_btn, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)

    def get_credentials(self):
        return self.username_input.text(), self.password_input.text()

class AttendanceApp(QWidget):
    def __init__(self, session=None):
        super().__init__()
        self.session = session or {"name": "Guest"}
        self.setWindowTitle("FixHR - Face Recognition Attendance System")
        
        # Responsive window sizing
        screen = QDesktopWidget().screenGeometry()
        if screen.width() >= 1920:
            self.setGeometry(50, 50, 1800, 1000)
        elif screen.width() >= 1366:
            self.setGeometry(50, 50, 1200, 800)
        else:
            self.setGeometry(50, 50, 1024, 700)
        
        self.setMinimumSize(800, 600)
        self.setStyleSheet(
            """
            QWidget { background-color: #001F3F; font-family: 'Segoe UI','Roboto',sans-serif; color: #ffffff; }
        """
        )
        try:
            self.setWindowIcon(QIcon(resource_path("fix_hr_prod_logo.png")))
        except:
            pass
        
        self.liveness_detector_loaded = False
        self.detect_and_predict = None
        self.fetch_thread = None
        self.liveness_loader_thread = None
        self.detect_worker_running = False
        self._detect_worker = None
        self.attendance_data = []
        self.cap = None
        self.auto_sync_timer = QTimer(self)
        self.auto_sync_timer.timeout.connect(self.check_auto_sync_schedule)
        self.guest_refresh_timer = QTimer(self)
        self.guest_refresh_timer.timeout.connect(self.update_guest_table)
        self.sync_settings = get_sync_settings()
        self.auto_sync_enabled = self.sync_settings["auto_sync_enabled"]
        self.auto_sync_time = self.sync_settings["auto_sync_time"]
        self.init_ui()
        self.init_timers()
        self.load_liveness_detector_async()
        self.backup_manager = BackupManager(
            db_path=resource_path("employees.db"),
        )
        self.apply_sync_settings(self.sync_settings)
        if is_logged_in():
            self.session = load_session()
            self.show_admin_view()
            print("Existing session loaded - Admin view activated")
        else:
            self.show_guest_view()
            print("No session found - Guest view activated")

    def resizeEvent(self, event):
        """Handle window resize events for responsive design"""
        super().resizeEvent(event)
        if hasattr(self, 'left_panel') and hasattr(self, 'right_panel'):
            window_width = self.width()
            
            # Adjust left panel size based on window width
            if window_width < 1024:
                self.left_panel.setFixedWidth(min(400, window_width - 100))
                if hasattr(self, 'camera_container'):
                    self.camera_container.setFixedSize(250, 250)
                    self.video_label.setFixedSize(230, 230)
                    self.video_label.setMask(self.create_circular_mask(230, 230))
            elif window_width < 1366:
                self.left_panel.setFixedWidth(450)
                if hasattr(self, 'camera_container'):
                    self.camera_container.setFixedSize(300, 300)
                    self.video_label.setFixedSize(280, 280)
                    self.video_label.setMask(self.create_circular_mask(280, 280))
            else:
                self.left_panel.setFixedWidth(500)
                if hasattr(self, 'camera_container'):
                    self.camera_container.setFixedSize(350, 350)
                    self.video_label.setFixedSize(330, 330)
                    self.video_label.setMask(self.create_circular_mask(330, 330))

    def show_admin_view(self):
        self.right_panel.setVisible(True)
        if hasattr(self, "guest_table_panel"):
            self.guest_table_panel.setVisible(False)
            self.right_panel.setVisible(True)
        if hasattr(self, "guest_refresh_timer"):
            self.guest_refresh_timer.stop()
        self.admin_login_btn.setText("Admin: Logged In")
        self.admin_login_btn.setStyleSheet(
            """
            QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #4caf50; border: none; border-radius: 4px; padding: 8px 16px; }
            QPushButton:hover { background-color: #388e3c; }
            """
        )
        self.logout_btn.setVisible(True)
        self.load_attendance_logs()
        new_sidebar = Sidebar(self.session)
        new_sidebar.date_selected.connect(self.update_table_by_date)
        self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
        self.sidebar = new_sidebar
        self.reset_face_detection_layout()
        self.data_refresh_timer.start(10000)
        self.left_panel.update()
        self.right_panel.update()
        self.apply_sync_settings()
        if hasattr(self, "guest_table"):
            self.guest_table.hide()

    def show_guest_view(self):
        """Enhanced show_guest_view method with responsive design"""
        self.right_panel.setVisible(False)
        self.admin_login_btn.setText("Admin Login")
        self.admin_login_btn.setStyleSheet(
            """
            QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
            QPushButton:hover { background-color: #303f9f; }
            """
        )
        self.logout_btn.setVisible(False)
        self.employee_card.update_value("[Employee Name]")
        self.data_refresh_timer.stop()
        self.update_face_detection_layout()
        if hasattr(self, "auto_sync_timer"):
            self.auto_sync_timer.stop()
        if hasattr(self, "guest_table_panel"):
            self.guest_table_panel.setVisible(True)
            self.right_panel.setVisible(False)
            self.update_guest_table()
        if hasattr(self, "guest_refresh_timer"):
            self.guest_refresh_timer.start(30000)

    def apply_sync_settings(self, settings=None):
        settings = settings or get_sync_settings()
        self.sync_settings = settings
        self.auto_sync_enabled = settings["auto_sync_enabled"]
        self.auto_sync_time = settings["auto_sync_time"]
        if self.auto_sync_enabled and is_logged_in():
            if not self.auto_sync_timer.isActive():
                self.auto_sync_timer.start(60000)
        else:
            self.auto_sync_timer.stop()

    def check_auto_sync_schedule(self):
        if not getattr(self, "auto_sync_enabled", False):
            return
        if not is_logged_in():
            return
        target_time = self.auto_sync_time or "09:00"
        try:
            target_hour, target_minute = [int(v) for v in target_time.split(":")]
        except ValueError:
            target_hour, target_minute = 9, 0
        now = datetime.datetime.now()
        today_str = now.strftime("%d-%m-%Y")
        last_run = get_setting("auto_sync_last_run", "")
        if last_run == today_str:
            return
        if (now.hour, now.minute) >= (target_hour, target_minute):
            print(f"[INFO] Auto sync triggered at {now.strftime('%H:%M')} with mode {self.sync_settings['sync_mode']}")
            # Use BackgroundSyncThread for auto sync with completion notification
            if not hasattr(self, "auto_sync_thread") or not self.auto_sync_thread or not self.auto_sync_thread.isRunning():
                self.auto_sync_thread = BackgroundSyncThread(sync_mode=self.sync_settings.get("sync_mode"))
                self.auto_sync_thread.finished.connect(self.on_auto_sync_finished)
                self.auto_sync_thread.start()
            threading.Thread(target=retry_failed_sync, daemon=True).start()
            set_setting("auto_sync_last_run", today_str)
            self.refresh_data()
    
    def on_auto_sync_finished(self, result):
        """Handle auto sync completion and show popup"""
        records_synced = result.get("records_synced", 0)
        records_failed = result.get("records_failed", 0)
        
        if result.get("success"):
            message = f"Auto Sync Completed!\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Auto sync completed successfully.")
            QMessageBox.information(self, "Auto Sync Complete", message)
        else:
            message = f"Auto Sync Completed with Issues\n\n"
            message += f"✅ Records Synced: {records_synced}\n"
            message += f"❌ Records Failed: {records_failed}\n\n"
            message += result.get("message", "Auto sync failed. Please check logs.")
            QMessageBox.warning(self, "Auto Sync Issue", message)
        
        self.refresh_data()

    def open_settings_dialog(self):
        if not is_logged_in():
            QMessageBox.warning(self, "Admin Required", "Please log in to configure sync settings.")
            return
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self.on_settings_updated)
        dialog.sync_completed.connect(lambda _: self.refresh_data())
        dialog.exec_()

    def on_settings_updated(self, settings):
        self.apply_sync_settings(settings)
        self.refresh_data()

    def create_circular_mask(self, width, height):
        region = QRegion(0, 0, width, height, QRegion.Ellipse)
        return region

    def create_rectangular_mask(self, width, height):
        region = QRegion(0, 0, width, height, QRegion.Rectangle)
        return region

    def build_guest_table_panel(self):
        panel = QFrame()
        panel.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            """
        )
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        title = QLabel("Today's Attendance Snapshot")
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #212121;")
        panel_layout.addWidget(title)

        self.guest_table = QTableWidget()
        self.guest_table.setColumnCount(8)
        self.guest_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Emp Code",
                "Name",
                "Check-in",
                "Check-out",
                "Status",
                "Mode",
                "Sync",
            ]
        )
        header = self.guest_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.guest_table.setAlternatingRowColors(True)
        self.guest_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.guest_table.verticalHeader().setVisible(False)
        self.guest_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.guest_table.setFocusPolicy(Qt.NoFocus)
        self.guest_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 9px;
                color: #333333;
            }
            QHeaderView::section {
                background: #f5f5f5;
                border: none;
                font-size: 9px;
                color: #555555;
                padding: 4px;
            }
            """
        )
        self.guest_table.setMaximumHeight(240)
        panel_layout.addWidget(self.guest_table)

        self.guest_table_hint = QLabel("")
        self.guest_table_hint.setStyleSheet("font-size: 9px; color: #757575;")
        panel_layout.addWidget(self.guest_table_hint)

        return panel

    def update_guest_table(self):
        if not hasattr(self, "guest_table") or not self.guest_table.isVisible():
            return
        logs = get_attendance_logs()
        self.guest_table.setRowCount(0)
        max_rows = 12
        for idx, log in enumerate(logs[:max_rows]):
            self.guest_table.insertRow(idx)
            row_data = [
                format_date_ddmmyy(log["checkin_date"]),
                str(log["emp_code"]),
                log["emp_full_name"],
                log["checkin_time"],
                log["checkout_time"] if log["checkout_time"] else "-",
                log["status"] if log["status"] else "Pending",
                log.get("mode", "Offline-Face"),
                "Synced" if log.get("sync", 0) == 1 else "Not Synced",
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                self.guest_table.setItem(idx, col, item)
        if logs:
            self.guest_table_hint.setText(f"Showing {min(len(logs), max_rows)} record(s) for today.")
        else:
            self.guest_table_hint.setText("No punches yet today.")

    def closeEvent(self, event):
        if hasattr(self, "backup_manager"):
            self.backup_manager.stop()
        if hasattr(self, "cap") and self.cap is not None:
            self.cap.release()
        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "detect_timer"):
            self.detect_timer.stop()
        if hasattr(self, "data_refresh_timer"):
            self.data_refresh_timer.stop()
        if hasattr(self, "auto_sync_timer"):
            self.auto_sync_timer.stop()
        if hasattr(self, "fetch_thread") and self.fetch_thread:
            self.fetch_thread.quit()
            self.fetch_thread.wait()
        if hasattr(self, "liveness_loader_thread") and self.liveness_loader_thread:
            self.liveness_loader_thread.quit()
            self.liveness_loader_thread.wait()
        event.accept()

    def load_liveness_detector_async(self):
        if self.liveness_loader_thread and self.liveness_loader_thread.isRunning():
            return
        self.start_btn.setEnabled(False)
        self.liveness_loader_thread = LivenessLoaderThread()
        self.liveness_loader_thread.finished.connect(self.on_liveness_detector_loaded)
        self.liveness_loader_thread.start()

    def on_liveness_detector_loaded(self, success, message, detector_function):
        if success:
            self.detect_and_predict = detector_function
            self.liveness_detector_loaded = True
            self.start_btn.setEnabled(True)
        else:
            self.liveness_detector_loaded = False
            self.start_btn.setEnabled(False)
            print("Detector failed to load")
            QMessageBox.critical(
                self, "Error", f"Failed to load liveness detector: {message}"
            )

    def fetch_employees(self):
        if not is_logged_in():
            QMessageBox.warning(self, "Access Denied", "Please login first to fetch employees.")
            return
        if self.fetch_thread and self.fetch_thread.isRunning():
            QMessageBox.information(
                self, "Info", "Employee fetch is already in progress..."
            )
            return
        self.sidebar.fetch_btn.setEnabled(False)
        self.fetch_thread = FetchThread(self.session.get("token", ""))
        self.fetch_thread.finished.connect(
            lambda success, msg: self.on_fetch_completed(success, msg)
        )
        self.fetch_thread.start()

    def on_fetch_completed(self, success, message):
        if hasattr(self.sidebar, 'fetch_btn'):
            self.sidebar.fetch_btn.setEnabled(True)
        if success:
            # Show loader and build/rebuild profiles right after fetching employees
            loader = ModalLoader("Loading Profiles", "Preparing face database for recognition...", self)
            thread = BuildIndexThread()
            def on_done(_info):
                loader.accept()
                QMessageBox.information(self, "Success", message)
            def on_err(err):
                loader.accept()
                QMessageBox.warning(self, "Profiles", f"Failed to prepare profiles: {err}")
                QMessageBox.information(self, "Success", message)
            thread.finished.connect(on_done)
            thread.error.connect(on_err)
            thread.start()
            loader.exec_()
            thread.wait()
        else:
            print("Fetch failed")
            QMessageBox.critical(self, "Error", f"Failed to fetch employees: {message}")

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            clear_session()
            self.session = {"name": "Guest"}
            self.data_refresh_timer.stop()
            self.show_guest_view()
            new_sidebar = Sidebar(self.session)
            new_sidebar.date_selected.connect(self.update_table_by_date)
            main_layout = self.layout()
            old_sidebar = main_layout.itemAt(0).widget()
            main_layout.replaceWidget(old_sidebar, new_sidebar)
            old_sidebar.deleteLater()
            self.sidebar = new_sidebar
            QMessageBox.information(self, "Success", "Successfully logged out!")
            print("Logged out successfully - showing compact guest view")

    def update_face_detection_layout(self):
        """Responsive guest view layout - centered with compact size"""
        self.content_layout.setAlignment(self.left_panel, Qt.AlignTop | Qt.AlignHCenter)
        
        # Use compact sizes (same as admin view but centered)
        window_width = self.width()
        if window_width < 1024:
            panel_width = 350
            camera_size = 250
            video_size = 230
        elif window_width < 1366:
            panel_width = 400
            camera_size = 300
            video_size = 280
        else:
            panel_width = 500
            camera_size = 350
            video_size = 330
        
        self.left_panel.setFixedWidth(panel_width)
        self.left_panel.setMaximumHeight(16777215)
        self.left_panel.setStyleSheet("""
            QFrame { 
                background-color: #ffffff;
                border: none;
            }
        """)
        
        # Remove any shadow effects for compact view
        if hasattr(self.left_panel, 'graphicsEffect'):
            self.left_panel.setGraphicsEffect(None)
        
        self.camera_container.setFixedSize(camera_size, camera_size)
        self.video_label.setFixedSize(video_size, video_size)
        self.video_label.setMask(self.create_circular_mask(video_size, video_size))
        
        # Compact positioning within the centered panel
        self.live_label.move(10, 15)
        self.live_dot.move(0, 15)
        self.employee_card.move(max(0, panel_width - 260), camera_size + 20)
        self.device_info_label.move(10, camera_size + 60)
        self.camera_container.move((panel_width - camera_size) // 2, 50)
        
        # Remove guest datetime display if exists (not needed in compact view)
        if hasattr(self, 'guest_date_label'):
            self.guest_date_label.hide()
        if hasattr(self, 'guest_time_label'):
            self.guest_time_label.hide()
        
        self.left_panel.update()
        print("Centered compact guest view layout updated")

    def create_guest_datetime_display(self):
        """Responsive date and time display"""
        if hasattr(self, 'guest_date_label'):
            self.guest_date_label.deleteLater()
        if hasattr(self, 'guest_time_label'):
            self.guest_time_label.deleteLater()

        panel_width = self.left_panel.width()
        
        self.guest_date_label = QLabel(self.left_panel)
        self.guest_date_label.setGeometry((panel_width - 180) // 2, 10, 180, 25)
        self.guest_date_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #007bff;
                background: transparent;
            }
        """)
        self.guest_date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.guest_time_label = QLabel(self.left_panel)
        self.guest_time_label.setGeometry((panel_width - 180) // 2, 35, 180, 30)
        self.guest_time_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #28a745;
                background: transparent;
            }
        """)
        self.guest_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.update_guest_datetime()

    def update_guest_datetime(self):
        """Update date and time for guest view"""
        if hasattr(self, 'guest_date_label') and hasattr(self, 'guest_time_label'):
            now = datetime.datetime.now()
            self.guest_date_label.setText(f"Date: {now.strftime('%d-%m-%Y')}")
            self.guest_time_label.setText(f"{now.strftime('%H:%M:%S')}")

    def update_time(self):
        """Enhanced update_time method to handle both admin and guest views"""
        now = datetime.datetime.now()
        
        if hasattr(self, 'time_label') and hasattr(self, 'date_label'):
            self.time_label.setText(now.strftime("%H:%M:%S"))
            self.date_label.setText(f"Date: {now.strftime('%d-%m-%y')}")
        
        if hasattr(self, 'guest_date_label') and hasattr(self, 'guest_time_label'):
            self.update_guest_datetime()

    def admin_login(self):
        if is_logged_in():
            reply = QMessageBox.question(
                self,
                "Session Active",
                "An admin session is already active. Do you want to log out the current session and log in again?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                clear_session()
                self.session = {"name": "Guest"}
                self.data_refresh_timer.stop()
                self.show_guest_view()
                new_sidebar = Sidebar(self.session)
                new_sidebar.date_selected.connect(self.update_table_by_date)
                self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
                self.sidebar = new_sidebar
            else:
                return

        dialog = LoginDialog()
        if dialog.exec_() == QDialog.Accepted:
            email, password = dialog.get_credentials()
            result = login_fixhr(email, password)
            if result["status"] == "success":
                self.session = result["data"]
                self.show_admin_view()
                QMessageBox.information(self, "Success", "Admin login successful")
                print("Admin logged in - showing right panel with responsive overview")
            else:
                self.show_guest_view()
                QMessageBox.critical(
                    self, "Login Failed", result.get("message", "Unknown error")
                )
        else:
            self.show_guest_view()

    def reset_face_detection_layout(self):
        """Responsive admin layout"""
        self.content_layout.setAlignment(self.left_panel, Qt.AlignLeft)
        
        window_width = self.width()
        if window_width < 1024:
            self.left_panel.setFixedWidth(350)
            camera_size = 250
            video_size = 230
        elif window_width < 1366:
            self.left_panel.setFixedWidth(400)
            camera_size = 300
            video_size = 280
        else:
            self.left_panel.setFixedWidth(500)
            camera_size = 350
            video_size = 330
        
        self.left_panel.setMaximumHeight(16777215)
        self.camera_container.setFixedSize(camera_size, camera_size)
        self.video_label.setFixedSize(video_size, video_size)
        self.video_label.setMask(self.create_circular_mask(video_size, video_size))
        
        # Responsive positioning for admin view
        self.live_label.move(10, 15)
        self.live_dot.move(0, 15)
        self.employee_card.move(max(0, self.left_panel.width() - 260), camera_size + 20)
        self.device_info_label.move(10, camera_size + 60)
        
        self.left_panel.update()
        print("Responsive admin layout applied")

    def create_overview_cards(self):
        """Responsive overview cards"""
        for i in reversed(range(self.overview_grid.count())):
            widget = self.overview_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        summary = get_daily_attendance_summary()
        total_emp = get_employee_count()
        present_today = summary["checked_in_only"] + summary["completed_attendance"]
        last_sync_str, next_sync_str = get_sync_status_overview()
        
        window_width = self.width()
        compact_mode = window_width < 1366
        
        cards = [
            ("Total Employees", str(total_emp), "All active staff members", "#E3F2FD", "#1E88E5", "👥"),
            ("Present Today", str(present_today), "Checked-in employees", "#E8F5E9", "#2E7D32", "✅"),
            ("Last DB Sync", last_sync_str, "", "#FFF8E1", "#FF8C00", "🗄️"),
            ("Next Sync", next_sync_str, "", "#FCE4EC", "#D81B60", "⏳"),
        ]
        
        # Responsive grid layout
        cols = 2 if compact_mode else 4
        for i, (title, value, sub, bg, fg, icon_text) in enumerate(cards):
            row = i // cols
            col = i % cols
            card = self.make_overview_card(title, value, sub, bg, fg, icon_text, compact=compact_mode)
            self.overview_grid.addWidget(card, row, col)

    def make_overview_card(self, title, number, sub, bg, fg, icon_text, compact=False):
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 100))
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        padding = 12 if compact else 16
        v.setContentsMargins(padding, padding, padding, padding)
        v.setSpacing(6 if compact else 8)

        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignCenter)
        icon_size = 30 if compact else 40
        icon.setFixedSize(icon_size, icon_size)
        icon.setStyleSheet(f"""
            QLabel {{
                background: rgba(255,255,255,0.8);
                border-radius: {icon_size//2}px;
                font-size: {14 if compact else 18}px;
                color: {fg};
                font-weight: 700;
            }}
        """)

        if compact:
            t = QLabel(title)
            t.setStyleSheet(f"font-size: 10px; color: {fg}; font-weight: 600;")
            n = QLabel(str(number))
            n.setStyleSheet(f"font-size: 11px; color: {fg}; font-weight: 500;")
            s = QLabel(sub)
            s.setStyleSheet(f"font-size: 9px; color: {fg};")
        else:
            t = QLabel(title)
            t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
            n = QLabel(str(number))
            n.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
            s = QLabel(sub)
            s.setStyleSheet(f"font-size: 10px; color: {fg};")
        
        t.setWordWrap(True)
        n.setWordWrap(True)
        s.setWordWrap(True)

        top_h = QHBoxLayout()
        top_h.setSpacing(8)
        top_h.addWidget(icon, 0, Qt.AlignLeft)
        top_h.addWidget(t, 0, Qt.AlignVCenter)
        top_h.addStretch()
        
        v.addLayout(top_h)
        v.addWidget(n)
        if sub:
            v.addWidget(s)

        return card

    def get_pending_sync_count(self):
        remaining = get_remaining_sync_count()
        return remaining["remaining_sync_count"]

    def refresh_data(self):
        if not is_logged_in():
            return
        try:
            self.create_overview_cards()
            pending = self.get_pending_sync_count()
            failed = len(get_failed_sync_records())
            self.alert_msg.setText(f"{pending} pending sync | {failed} failed")
            # Refresh the attendance table to show updated sync status
            if hasattr(self, 'load_attendance_logs'):
                self.load_attendance_logs()
        except Exception as e:
            print(f"Error refreshing cards: {e}")

    def update_attendance_table(self):
        self.daily_table.setRowCount(0)
        emp_code = self.session.get("employee_id", None)
        for entry in self.attendance_data:
            if is_logged_in() or (emp_code and entry[0][0] == str(emp_code)):
                row_pos = self.daily_table.rowCount()
                self.daily_table.insertRow(row_pos)
                for col, (text, font, color) in enumerate(entry):
                    item = QTableWidgetItem(text)
                    item.setFont(font)
                    item.setForeground(QColor(color))
                    self.daily_table.setItem(row_pos, col, item)
        self.daily_table.scrollToTop()

    def toggle_blink(self):
        if self.online_status:
            if self.blink_state:
                self.live_dot.setStyleSheet(
                    """
                    QLabel {
                        background-color: #4caf50;
                        border-radius: 12px;
                        border: 3px solid #a5d6a7;
                    }
                """
                )
            else:
                self.live_dot.setStyleSheet(
                    """
                    QLabel {
                        background-color: transparent;
                        border-radius: 12px;
                        border: 3px solid #a5d6a7;
                    }
                """
                )
        else:
            self.live_dot.setStyleSheet(
                """
                QLabel {
                    background-color: red;
                    border-radius: 12px;
                    border: 3px solid #ef9a9a;
                }
            """
            )
        self.blink_state = not self.blink_state

    def update_internet_status(self):
        online = is_internet_available()
        self.online_status = online
        self.live_label.setText("Live" if online else "Offline")
        self.device_info_label.setText(
            f"Device Name: {self.device_info_data['device_name']}\n"
            f"Device Model: {self.device_info_data['device_model']}\n"
            f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
            f"Internet Status: {'Online' if online else 'Offline'}"
        )

    def update_camera_border(self, recognition_status):
        self.camera_container.setStyleSheet(
            "QFrame { background: transparent; border: none; border-radius: 200px; }"
        )
        glow = QGraphicsDropShadowEffect(self.camera_container)
        glow.setOffset(0, 0)
        glow.setBlurRadius(40)
        if recognition_status == "recognized":
            color = QColor("#4caf50")
        elif recognition_status == "detecting":
            color = QColor("#ff9800")
        elif recognition_status == "failed":
            color = QColor("#f44336")
        else:
            color = QColor("#3f51b5")
        glow.setColor(color)
        self.camera_container.setGraphicsEffect(glow)
        
        self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
        self.glow_animation.setStartValue(20)
        self.glow_animation.setEndValue(80)
        self.glow_animation.setDuration(1000)
        self.glow_animation.setLoopCount(-1)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.glow_animation.start()

    def reset_camera_border_after_delay(self):
        QTimer.singleShot(3000, lambda: self.update_camera_border("default"))

    def on_recognition_success(self, employee_name):
        self.employee_card.update_value(employee_name)
        self.update_camera_border("recognized")
        self.reset_camera_border_after_delay()
        print(f"Recognition successful: {employee_name}")

    def on_recognition_failed(self):
        self.employee_card.update_value("Unknown Person")
        self.update_camera_border("failed")
        self.reset_camera_border_after_delay()
        print("Recognition failed")

    def on_detection_started(self):
        self.update_camera_border("detecting")
        print("Detection started")

    def on_detection_stopped(self):
        self.update_camera_border("default")
        print("Detection stopped")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar(self.session)
        self.sidebar.date_selected.connect(self.update_table_by_date)
        main_layout.addWidget(self.sidebar)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f5f5;")
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_content_layout = QVBoxLayout(content_widget)
        self.main_content_layout.setSpacing(0)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)

        header_card = ModernCard()
        header_card.setMinimumHeight(50)
        header_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_card.setStyleSheet(
            """
            QFrame { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 0px; }
        """
        )
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(12)

        header_title = QLabel("Face Recognition Attendance System")
        header_title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #ff9800; background: transparent; padding-top: 4px;"
        )
        header_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout.addWidget(header_title, 0, Qt.AlignTop | Qt.AlignLeft)

        self.admin_login_btn = QPushButton("Admin Login")
        self.admin_login_btn.setCursor(Qt.PointingHandCursor)
        self.admin_login_btn.setFixedHeight(28)
        self.admin_login_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.admin_login_btn.setStyleSheet(
            """
            QPushButton { font-size: 11px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 6px 12px; margin-top: 4px; }
            QPushButton:hover { background-color: #303f9f; }
        """
        )
        self.admin_login_btn.clicked.connect(self.admin_login)
        header_layout.addStretch()
        header_layout.addWidget(self.admin_login_btn, 0, Qt.AlignTop | Qt.AlignRight)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedHeight(28)
        self.logout_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.logout_btn.setStyleSheet(
            """
            QPushButton { font-size: 11px; font-weight: 500; color: #ffffff; background-color: #f44336; border: none; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #d32f2f; }
            """
        )
        self.logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_btn, 0, Qt.AlignTop | Qt.AlignRight)
        self.logout_btn.setVisible(False)

        self.main_content_layout.addWidget(header_card)

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(6)

        self.left_panel = QFrame()
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.left_panel.setStyleSheet(
            """
            QFrame { background-color: #ffffff; border: none; }
        """
        )
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(6, 0, 6, 6)
        left_layout.setSpacing(0)
        self.left_layout = left_layout

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)

        self.live_dot = QLabel()
        self.live_dot.setFixedSize(20, 20)
        self.live_dot.setStyleSheet(
            """
            QLabel {
                background-color: #4caf50;
                border-radius: 10px;
                border: 2px solid #a5d6a7;
            }
        """
        )
        self.live_label = QLabel("Live")
        self.live_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: 600;
            color: #212121;
            border: none;
            margin-top: 0px;
        """
        )
        self.live_label.setAlignment(Qt.AlignVCenter)

        live_header = QHBoxLayout()
        live_header.setContentsMargins(0, 0, 0, 0)
        live_header.setSpacing(4)
        live_header.addWidget(self.live_dot, 0, Qt.AlignVCenter)
        live_header.addWidget(self.live_label, 0, Qt.AlignVCenter)

        self.blink_state = True
        self.online_status = True
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(600)
        self.internet_timer = QTimer()
        self.internet_timer.timeout.connect(self.update_internet_status)
        self.internet_timer.start(5000)

        self.employee_card = StatusCard("Employee", "[Employee Name]", "#4caf50")
        self.employee_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        header_row.addLayout(live_header)
        header_row.addStretch()
        header_row.addWidget(self.employee_card)
        left_layout.addLayout(header_row)
        left_layout.addSpacing(8)

        self.camera_container = QFrame()
        self.camera_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.camera_container.setStyleSheet(
            "QFrame { background: transparent; border-radius: 175px; }"
        )
        camera_layout = QVBoxLayout(self.camera_container)
        camera_layout.setContentsMargins(8, 8, 8, 8)
        
        self.video_label = QLabel("Waiting for camera connection")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setWordWrap(True)
        self.video_label.setStyleSheet(
            "QLabel { background-color: transparent; border: none; }"
        )
        
        camera_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.camera_container, alignment=Qt.AlignCenter)
        left_layout.addSpacing(8)

        self.device_info_data = get_device_info()
        self.device_info_label = QLabel(
            f"Device Name: {self.device_info_data['device_name']}\n"
            f"Device Model: {self.device_info_data['device_model']}\n"
            f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
            f"Internet Status: {self.device_info_data.get('internet_status','Unknown')}"
        )
        self.device_info_label.setStyleSheet(
            "font-size: 12px; font-weight: 500; color: #212121; border: none; margin-top: 4px;"
        )
        self.device_info_label.setWordWrap(True)
        self.device_info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout.addWidget(self.device_info_label)
        left_layout.addSpacing(8)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)
        button_layout.setSpacing(8)

        self.start_btn = QPushButton("Start Detection")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 12px;
                font-weight: 500;
                color: white;
                background: #4caf50;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #388e3c; }
            QPushButton:pressed { background: #2e7d32; }
            QPushButton:disabled { background: #bdbdbd; color: #ffffff; }
        """
        )
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.toggle_detection)

        reset_btn = QPushButton("Reset")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedHeight(40)
        reset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        reset_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 12px;
                font-weight: 500;
                color: #757575;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #f5f5f5; border: 1px solid #bdbdbd; color: #424242; }
            QPushButton:pressed { background-color: #eeeeee; }
        """
        )
        button_layout.addWidget(self.start_btn, 2)
        button_layout.addWidget(reset_btn, 1)
        left_layout.addLayout(button_layout)

        self.content_layout.addWidget(self.left_panel)

        self.guest_table_panel = self.build_guest_table_panel()
        self.guest_table_panel.setVisible(False)
        self.left_layout.addWidget(self.guest_table_panel)

        self.right_panel = ModernCard()
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_panel.setStyleSheet(
            """
            QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
        """
        )
        self.right_panel.setVisible(False)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        top_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_lbl = QLabel("Offline Attendance")
        title_lbl.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            color: #212121;
            background: transparent;
            border: none;
        """
        )
        subtitle_lbl = QLabel("Overview")
        subtitle_lbl.setStyleSheet(
            """
            font-size: 10px;
            font-weight: 350;
            color: #212121;
            background: transparent;
            border: none;
        """
        )
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)
        top_row.addLayout(title_col)
        top_row.addStretch()

        dt_row = QHBoxLayout()
        dt_row.setSpacing(6)
        dt_row.setContentsMargins(0, 0, 0, 0)
        self.date_label = QLabel("Date: --- --- --")
        self.date_label.setStyleSheet(
            """
            font-size: 12px;
            font-weight: 500;
            color: #1565c0;
            background: transparent;
            border: none;
        """
        )
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet(
            """
            font-size: 12px;
            font-weight: 500;
            color: #1565c0;
            background: transparent;
            border: none;
        """
        )
        dt_row.addWidget(self.date_label, 0, Qt.AlignRight)
        dt_row.addWidget(self.time_label, 0, Qt.AlignRight)
        top_row.addLayout(dt_row)
        right_layout.addLayout(top_row)

        self.overview_grid = QGridLayout()
        self.overview_grid.setHorizontalSpacing(8)
        self.overview_grid.setVerticalSpacing(8)
        self.create_overview_cards()
        right_layout.addLayout(self.overview_grid)

        section1_header = QHBoxLayout()
        title_alert_layout = QHBoxLayout()
        title_alert_layout.setSpacing(10)
        s1_title = QLabel("Daily Attendance Log")
        s1_title.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            color: #212121;
            background: transparent;
            border: none;
        """
        )
        title_alert_layout.addWidget(s1_title)
        
        alert_container = QWidget()
        alert_layout = QHBoxLayout(alert_container)
        alert_layout.setContentsMargins(0, 0, 0, 0)
        alert_layout.setSpacing(4)
        alert_icon = QLabel("⚠️")
        alert_icon.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #FF8C00;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """
        )
        pending_sync_count = self.get_pending_sync_count()
        self.alert_msg = QLabel(f"{pending_sync_count} records pending sync")
        self.alert_msg.setStyleSheet(
            """
            QLabel {
                font-size: 10px;
                color: #FF8C00;
                background: transparent;
                border: none;
                padding: 0px;
                font-weight: 500;
            }
        """
        )
        alert_layout.addWidget(alert_icon)
        alert_layout.addWidget(self.alert_msg)
        title_alert_layout.addWidget(alert_container)
        section1_header.addLayout(title_alert_layout)
        section1_header.addStretch()

        search_container = QWidget()
        search_container.setFixedWidth(180)
        search_container.setStyleSheet(
            """
            QWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: #ffffff;
            }
            QWidget:focus-within {
                border-color: #bdbdbd;
            }
        """
        )
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 0, 6, 0)
        search_layout.setSpacing(4)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search employee...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 11px;
                padding: 6px 0px;
                color: #000000;
            }
            QLineEdit:focus {
                border: none;
                outline: none;
                color: #000000;
            }
        """
        )
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #9e9e9e;
                background: transparent;
                border: none;
            }
        """
        )
        self.search_input.textChanged.connect(self.search_table)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_icon)
        section1_header.addWidget(search_container)
        right_layout.addLayout(section1_header)

        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(8)
        self.daily_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Emp Code",
                "Name",
                "Check-in",
                "Check-out",
                "Status",
                "Mode",
                "Sync",
            ]
        )
        header = self.daily_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft)
        self.daily_table.setAlternatingRowColors(True)
        self.daily_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.daily_table.verticalHeader().setVisible(False)
        self.daily_table.setSortingEnabled(True)
        self.daily_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.daily_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #d2e7f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 11px;
                color: #424242;
                gridline-color: #eeeeee;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #eeeeee;
                border-right: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #0d47a1;
                font-weight: 500;
            }
            QHeaderView::section {
                background: #001F3F;
                color: #ffffff;
                font-weight: 500;
                font-size: 10px;
                padding: 8px 12px;
                border: none;
                text-transform: uppercase;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 4px;
                min-height: 15px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: transparent;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

        right_layout.addWidget(self.daily_table)
        right_layout.addItem(
            QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        self.content_layout.addWidget(self.right_panel, 2)
        self.main_content_layout.addLayout(self.content_layout)
        main_layout.addWidget(content_widget, 1)
        self.load_attendance_logs()

    def search_table(self, text):
        text = text.strip().lower()
        for row in range(self.daily_table.rowCount()):
            match = False
            for col in range(self.daily_table.columnCount()):
                item = self.daily_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.daily_table.setRowHidden(row, not match)

    def init_timers(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")
        except Exception as e:
            print("Camera unavailable")
            self.start_btn.setEnabled(False)
            QMessageBox.critical(self, "Error", f"Failed to initialize camera: {e}")
            self.cap = None
            return
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
        self.detect_timer = QTimer()
        self.detect_timer.timeout.connect(self.detect)
        
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)
        
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.refresh_data)
        
        self.is_detecting = False
        self.update_time()

    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            print("Camera unavailable")
            self.video_label.setText("No Camera")
            return
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                print("Failed to capture frame")
                self.video_label.setText("No Frame")
                return
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            pixmap = pixmap.scaled(
                self.video_label.width(), self.video_label.height(),
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.video_label.setPixmap(pixmap)
            self.video_label.setText("")
        except Exception as e:
            print("Frame update error")
            self.video_label.setText("Error")

    def toggle_detection(self):
        if not self.liveness_detector_loaded:
            QMessageBox.warning(
                self,
                "Warning",
                "Liveness detector is not loaded yet. Please wait for it to load.",
            )
            return
        if self.cap is None or not self.cap.isOpened():
            QMessageBox.warning(
                self,
                "Warning",
                "Camera is not available. Please check the camera connection.",
            )
            return
        if self.is_detecting:
            self.detect_timer.stop()
            self.start_btn.setText("Start Detection")
            self.start_btn.setStyleSheet(
                """
                QPushButton { font-size: 12px; font-weight: 500; color: white; background: #4caf50; border: none; border-radius: 4px; padding: 10px 20px; }
                QPushButton:hover { background: #388e3c; }
            """
            )
            print("Detection stopped")
        else:
            self.detect_timer.start(1000)
            self.start_btn.setText("Stop Detection")
            self.start_btn.setStyleSheet(
                """
                QPushButton { font-size: 12px; font-weight: 500; color: white; background: #f44336; border: none; border-radius: 4px; padding: 10px 20px; }
                QPushButton:hover { background: #d32f2f; }
            """
            )
        self.is_detecting = not self.is_detecting

    def detect(self):
        if not self.liveness_detector_loaded or self.detect_and_predict is None:
            return
        if self.cap is None or not self.cap.isOpened():
            return
        if getattr(self, "detect_worker_running", False):
            return
        ret, frame = self.cap.read()
        if not ret or frame is None or frame.size == 0:
            return
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            frame = (
                cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                if len(frame.shape) == 2
                else frame
            )
        self.detect_worker_running = True
        self._detect_worker = DetectWorker(self.detect_and_predict, frame)
        self._detect_worker.result_ready.connect(self.on_detect_result)
        self._detect_worker.finished.connect(
            lambda: setattr(self, "detect_worker_running", False)
        )
        self._detect_worker.start()

    def on_detect_result(self, result):
        try:
            if result.get("status"):
                if is_logged_in():
                    self.load_attendance_logs()
                name = result.get("emp_full_name", "Employee")
                self.employee_card.update_value(name)
                self.update_camera_border("recognized")
                self.reset_camera_border_after_delay()
                speak("Hello " + name)
                if is_logged_in():
                    self.daily_table.scrollToTop()
                elif hasattr(self, "guest_table") and self.guest_table.isVisible():
                    self.update_guest_table()
            else:
                name = result.get("emp_full_name", "Unknown")
                self.employee_card.update_value(name)
                msg = result.get("message", "")
                if msg and "detect" in msg.lower():
                    self.update_camera_border("detecting")
                else:
                    self.update_camera_border("failed")
                    self.reset_camera_border_after_delay()
        except Exception:
            pass

    def resume_detection(self):
        if self.is_detecting:
            print("Scanning for faces...")
            self.detect_timer.start(1000)

    def load_attendance_logs(self):
        if not is_logged_in():
            return
        logs = get_attendance_logs()
        current_scroll_pos = self.daily_table.verticalScrollBar().value()
        selected_rows = [index.row() for index in self.daily_table.selectionModel().selectedRows()]
        self.daily_table.setRowCount(0)
        
        if hasattr(self, "date_label"):
            self.date_label.setText(
                f"Date: {datetime.datetime.now().strftime('%d-%m-%y')}"
            )
        
        for log in logs:
            row_pos = self.daily_table.rowCount()
            self.daily_table.insertRow(row_pos)
            row_data = [
                format_date_ddmmyy(log["checkin_date"]),
                str(log["emp_code"]),
                log["emp_full_name"],
                log["checkin_time"],
                log["checkout_time"] if log["checkout_time"] else "-",
                log["status"] if log["status"] else "Pending",
                log.get("mode", "Offline-Face"),
                "Synced" if log.get("sync", 0) == 1 else "Not Synced",
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                if col == 5:
                    if text == "CHECKED_IN":
                        item = QTableWidgetItem("MSP")
                        item.setForeground(QColor("orange"))
                    elif text == "CHECKED_OUT":
                        item = QTableWidgetItem("Present")
                        item.setForeground(QColor("green"))
                    else:
                        item.setForeground(QColor("blue"))
                item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.daily_table.setItem(row_pos, col, item)
        
        self.daily_table.verticalScrollBar().setValue(current_scroll_pos)
        if selected_rows:
            for row in selected_rows:
                if row < self.daily_table.rowCount():
                    self.daily_table.selectRow(row)

    def update_table_by_date(self, selected_date):
        if not is_logged_in():
            return
        logs = get_attendance_by_date(selected_date)
        current_scroll_pos = self.daily_table.verticalScrollBar().value()
        selected_rows = [index.row() for index in self.daily_table.selectionModel().selectedRows()]
        
        if hasattr(self, "date_label"):
            self.date_label.setText(
                f"Date: {format_date_ddmmyy(selected_date)}"
            )
        
        self.daily_table.setRowCount(0)
        if logs:
            for log in logs:
                row_pos = self.daily_table.rowCount()
                self.daily_table.insertRow(row_pos)
                row_data = [
                    format_date_ddmmyy(log["checkin_date"]),
                    str(log["emp_code"]),
                    log["emp_full_name"],
                    log["checkin_time"],
                    log["checkout_time"] if log["checkout_time"] else "-",
                    log["status"] if log["status"] else "Pending",
                    log.get("mode", "Offline-Face"),
                    "Synced" if log.get("sync", 0) == 1 else "Not Synced",
                ]
                for col, text in enumerate(row_data):
                    item = QTableWidgetItem(text)
                    if col == 5:
                        if text == "CHECKED_IN":
                            item = QTableWidgetItem("MSP")
                            item.setForeground(QColor("orange"))
                        elif text == "CHECKED_OUT":
                            item = QTableWidgetItem("Present")
                            item.setForeground(QColor("green"))
                        else:
                            item.setForeground(QColor("blue"))
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    self.daily_table.setItem(row_pos, col, item)
        
        self.daily_table.verticalScrollBar().setValue(current_scroll_pos)
        if selected_rows:
            for row in selected_rows:
                if row < self.daily_table.rowCount():
                    self.daily_table.selectRow(row)
        else:
            print(f"No attendance found for {selected_date}")

def run_app():
    app = QApplication(sys.argv)
    
    # Enable high DPI scaling for responsive design
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    init_db()
    session = load_session() if is_logged_in() else {"name": "Guest"}
    window = AttendanceApp(session)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()