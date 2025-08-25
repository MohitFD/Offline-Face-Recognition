import os
import sys
import cv2
import datetime
import importlib.metadata
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
)
from PyQt5.QtCore import (
    QTimer,
    Qt,
    pyqtSignal,
    QThread,
    QSize,
    QDate,
    QPropertyAnimation,
    QEasingCurve,
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
    QRegion,  # Added for circular mask
)

# --- Your existing helpers (unchanged) ---
from fetch_emp_from_fixhr import fetch_and_store_employees
from login import login_fixhr, is_logged_in, load_session, clear_session
from database import (
    get_attendance_logs,
    get_daily_attendance_summary,
    get_employee_count,
    get_attendance_by_date,
    init_db,
)
from device_info import get_device_info, is_internet_available
from speak import speak
from backup_utils import BackupManager
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---------------------- Date Format Helpers ----------------------
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

# ---------------------- Threads ----------------------
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

# ---------------------- UI Helpers ----------------------
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
        self.setFixedHeight(80)
        self.setStyleSheet(
            f"""
            QFrame {{
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 12px;
                margin: 4px;
            }}
            QFrame:hover {{
            }}
        """
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            font-size: 13px; font-weight: 500; color: #757575; background: transparent;
        """
        )
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            """
            font-size: 15px; font-weight: 600; color: #212121; background: transparent;
        """
        )
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def update_value(self, value):
        self.value_label.setText(value)

class SidebarButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(45)
        self.setStyleSheet(self.get_default_style())

    def get_default_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                color: #ffffff;
                font-size: 14px;
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
                    padding: 10px 15px;
                    border: none;
                    border-radius: 6px;
                    background-color: #E3F2FD;
                    color: #1976d2;
                    font-size: 14px;
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
        radius = min(rect.width(), rect.height()) // 2 - 6
        accent = QColor("#0078D7")
        if is_today and not is_selected:
            painter.setBrush(QBrush(accent))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        elif is_selected:
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(accent, 2))
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        elif is_hovered:
            painter.setBrush(QBrush(QColor(0, 120, 215, 80)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
        else:
            painter.setPen(Qt.white)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

def get_app_version():
    try:
        return importlib.metadata.version("FixHR")
    except importlib.metadata.PackageNotFoundError:
        return "dev"

# ---------------- SIDEBAR CLASS ----------------
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
        self.setFixedWidth(self.expanded_width)
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
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        top_bar_layout.setSpacing(0)

        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(2)

        self.logo_label = QLabel("FixHR")
        self.logo_label.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #FF8C00; background: transparent;"
        )
        self.logo_label.setAlignment(Qt.AlignLeft)

        self.version_label = QLabel(f"v{get_app_version()}")
        self.version_label.setStyleSheet(
            "font-size: 11px; color: #ffffff; background: transparent;"
        )
        self.version_label.setAlignment(Qt.AlignLeft)

        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.version_label)
        top_bar_layout.addWidget(logo_frame, alignment=Qt.AlignLeft)

        top_bar_layout.addStretch()

        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.toggle_btn.setIconSize(QSize(28, 28))
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(
            """
            QToolButton {
                border: none;
                background-color: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 6px;
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
        layout.setSpacing(10)
        layout.setContentsMargins(10, 20, 5, 20)
        layout.setAlignment(Qt.AlignTop)

        user_info_frame = QFrame()
        user_info_frame.setStyleSheet("background: transparent;")
        user_info_layout = QVBoxLayout(user_info_frame)
        user_info_layout.setSpacing(6)
        user_info_layout.setContentsMargins(0, 0, 0, 0)

        user_avatar = QLabel("👤")
        user_avatar.setStyleSheet(
            """
            font-size: 60px;
            background-color: #002F5E;
            border-radius: 40px;
            padding: 8px;
            color: #F5F5F5;
            border: 2px solid #004080;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            """
        )
        user_avatar.setFixedSize(80, 80)
        user_avatar.setAlignment(Qt.AlignCenter)

        user_name = QLabel(f"Welcome, {self.session.get('name','User')}")
        user_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent;")
        user_name.setAlignment(Qt.AlignCenter)

        user_role = QLabel(self.session.get("role", "Employee"))
        user_role.setStyleSheet("font-size: 12px; color: #cccccc; background: transparent;")
        user_role.setAlignment(Qt.AlignCenter)

        user_info_layout.addWidget(user_avatar, alignment=Qt.AlignCenter)
        user_info_layout.addWidget(user_name, alignment=Qt.AlignCenter)
        user_info_layout.addWidget(user_role, alignment=Qt.AlignCenter)

        layout.addWidget(user_info_frame, alignment=Qt.AlignHCenter)

        layout.addSpacing(20)

        self.nav_label = QLabel("NAVIGATION")
        self.nav_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #9e9e9e; margin-bottom: 10px; background: transparent;"
        )
        layout.addWidget(self.nav_label, alignment=Qt.AlignLeft)

        self.nav_buttons = {}

        self.fetch_btn = QPushButton("Fetch Employees")
        self.fetch_btn.setCursor(Qt.PointingHandCursor)
        self.fetch_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #002F5E;
                color: white;
                border: none;
                padding: 6px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #004080;
            }
        """
        )
        self.fetch_btn.clicked.connect(lambda: self.parent().fetch_employees())
        layout.addWidget(self.fetch_btn, alignment=Qt.AlignLeft)

        layout.addStretch()

        self.cal_label = QLabel("CALENDAR")
        self.cal_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #9e9e9e; margin-bottom: 10px; background: transparent;"
        )
        layout.addWidget(self.cal_label, alignment=Qt.AlignLeft)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet(
            """
            QCalendarWidget {
                background-color: #001F3F;
                border: 1px solid #2c3e50;
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                font-size: 14px;
                background-color: #002F5E;
                border: none;
                margin: 1px;
                padding: 4px;
            }
            QCalendarWidget QMenu {
                background-color: #001F3F;
                color: white;
                border: 1px solid #2c3e50;
            }
            QCalendarWidget QMenu::item {
                background-color: #001F3F;
                color: white;
                padding: 5px 10px;
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
            self.cal_label.show()
            self.calendar.show()
            self.fetch_btn.show()
            self.is_collapsed = False
        else:
            self.setFixedWidth(self.collapsed_width)
            self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
            self.logo_label.hide()
            self.version_label.hide()
            self.nav_label.hide()
            self.cal_label.hide()
            self.calendar.hide()
            self.fetch_btn.hide()
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
        self.setFixedSize(800, 600)
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
        main_layout.setContentsMargins(100, 20, 100, 100)
        main_layout.setSpacing(30)
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                border-radius: 15px;
            }
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 10, 40, 40)
        container_layout.setSpacing(15)
        user_icon = QLabel()
        user_icon.setFixedSize(120, 120)
        pixmap = QPixmap(120, 120)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255), 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
        painter.drawEllipse(10, 10, 100, 100)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(45, 30, 30, 30)
        painter.setPen(QPen(QColor(255, 255, 255), 6))
        painter.drawArc(35, 65, 50, 35, 0, 180 * 16)
        painter.end()
        user_icon.setPixmap(pixmap)
        user_icon.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(user_icon, alignment=Qt.AlignCenter)
        container_layout.addSpacing(10)
        title_label = QLabel("FixHr User")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #FFFFFF;
                padding-bottom: 10px;
            }
        """
        )
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)
        username_layout = QVBoxLayout()
        username_label = QLabel("User name:")
        username_label.setStyleSheet(
            "font-size: 18px; color: #FFFFFF; margin-bottom: 5px;"
        )
        username_label.setAlignment(Qt.AlignLeft)
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 18px;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 250px;
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
            "font-size: 18px; color: #FFFFFF; margin-bottom: 5px;"
        )
        password_label.setAlignment(Qt.AlignLeft)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 18px;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                min-width: 250px;
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
                font-size: 20px;
                font-weight: bold;
                color: white;
                background-color: transparent;
                border: 2px solid #3f51b5;
                border-radius: 10px;
                padding: 15px 30px;
                min-width: 150px;
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

# ---------------------- Main App ----------------------
class AttendanceApp(QWidget):
    def __init__(self, session=None):
        super().__init__()
        self.session = session or {"name": "Guest", "role": "Employee"}
        self.setWindowTitle("FixHR - Face Recognition Attendance System")
        self.setGeometry(50, 50, 1800, 1000)
        self.setStyleSheet(
            """
            QWidget { background-color: #001F3F; font-family: 'Segoe UI','Roboto',sans-serif; color: #ffffff; }
        """
        )
        self.setWindowIcon(QIcon("C:/Users/Kesar/Documents/GitHub/Offline-Face-Recognition/fix_hr_prod_logo.png"))
        self.liveness_detector_loaded = False
        self.detect_and_predict = None
        self.fetch_thread = None
        self.liveness_loader_thread = None
        self.detect_worker_running = False
        self._detect_worker = None
        self.is_admin = False
        self.attendance_data = []
        self.cap = None
        self.init_ui()
        self.init_timers()
        self.load_liveness_detector_async()
        self.backup_manager = BackupManager(
            db_path="C:/Users/Kesar/Documents/GitHub/Offline-Face-Recognition/employees.db",
        )
        self.backup_manager.start()

    def create_circular_mask(self, width, height):
        """Create a circular QRegion for masking the video_label"""
        region = QRegion(0, 0, width, height, QRegion.Ellipse)
        return region

    def closeEvent(self, event):
        if hasattr(self, "backup_manager"):
            self.backup_manager.stop()
        if hasattr(self, "cap") and self.cap is not None:
            self.cap.release()
        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "detect_timer"):
            self.detect_timer.stop()
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
        if self.fetch_thread and self.fetch_thread.isRunning():
            QMessageBox.information(
                self, "Info", "Employee fetch is already in progress..."
            )
            return
        self.sidebar.fetch_btn.setEnabled(False)
        self.sidebar.fetch_btn.setText("Fetching...")
        self.fetch_thread = FetchThread(self.session.get("token", ""))
        self.fetch_thread.finished.connect(
            lambda success, msg: self.on_fetch_completed(success, msg)
        )
        self.fetch_thread.start()

    def on_fetch_completed(self, success, message):
        self.sidebar.fetch_btn.setEnabled(True)
        self.sidebar.fetch_btn.setText("Fetch Employees")
        if success:
            if self.liveness_detector_loaded and hasattr(self, "detect_and_predict"):
                try:
                    from recognition import force_rebuild_index
                    rebuild_success = force_rebuild_index()
                    if rebuild_success:
                        print("Ready - Faces loaded")
                    else:
                        print("Ready - No face images")
                except Exception:
                    print("Ready - Index rebuild failed")
            QMessageBox.information(self, "Success", message)
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
            # Clear session data
            clear_session()
            
            # Reset admin state
            self.is_admin = False
            
            # Hide right panel (admin view)
            self.right_panel.setVisible(False)
            
            # Reset session to guest
            self.session = {"name": "Guest", "role": "Employee"}
            
            # Create new sidebar with guest session
            new_sidebar = Sidebar(self.session)
            new_sidebar.date_selected.connect(self.update_table_by_date)
            
            # Replace the current sidebar with the new one
            main_layout = self.layout()
            old_sidebar = main_layout.itemAt(0).widget()
            main_layout.replaceWidget(old_sidebar, new_sidebar)
            old_sidebar.deleteLater()  # Clean up old sidebar
            self.sidebar = new_sidebar
            
            # Reset admin login button
            self.admin_login_btn.setText("Admin Login")
            self.admin_login_btn.setStyleSheet(
                """
                QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
                QPushButton:hover { background-color: #303f9f; }
            """
            )
            
            # Reset employee card
            self.employee_card.update_value("[Employee Name]")
            
            # Show success message
            QMessageBox.information(self, "Success", "Successfully logged out!")
            
            print("Logged out successfully - showing guest view with sidebar and face detection")

    def admin_login(self):
        # Check if already logged in
        if is_logged_in():
            reply = QMessageBox.question(
                self,
                "Session Active",
                "An admin session is already active. Do you want to log out the current session and log in again?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                clear_session()  # Clear existing session
                self.session = {"name": "Guest", "role": "Employee"}  # Reset to guest
                self.is_admin = False
                self.right_panel.setVisible(False)
                # Update sidebar to reflect guest state
                new_sidebar = Sidebar(self.session)
                new_sidebar.date_selected.connect(self.update_table_by_date)
                self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
                self.sidebar = new_sidebar
            else:
                return  # Exit if user chooses not to log out

        # Show login dialog
        dialog = LoginDialog()
        if dialog.exec_() == QDialog.Accepted:
            email, password = dialog.get_credentials()
            result = login_fixhr(email, password)
            if result["status"] == "success":
                self.session = result["data"]
                self.is_admin = True
                self.right_panel.setVisible(True)  # Show four-box overview and attendance table
                self.load_attendance_logs()  # Populate daily attendance table
                self.admin_login_btn.setText("Admin: Logged In")
                self.admin_login_btn.setStyleSheet(
                    """
                    QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #4caf50; border: none; border-radius: 4px; padding: 8px 16px; }
                    QPushButton:hover { background-color: #388e3c; }
                    """
                )
                # Update sidebar with new session data
                new_sidebar = Sidebar(self.session)
                new_sidebar.date_selected.connect(self.update_table_by_date)
                self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
                self.sidebar = new_sidebar
                QMessageBox.information(self, "Success", "Admin login successful")
                print("Admin logged in - showing right panel with four-box overview and daily attendance")
            else:
                self.is_admin = False
                self.right_panel.setVisible(False)
                QMessageBox.critical(
                    self, "Login Failed", result.get("message", "Unknown error")
                )
        else:
            self.is_admin = False
            self.right_panel.setVisible(False)
            self.admin_login_btn.setText("Admin Login")
            self.admin_login_btn.setStyleSheet(
                """
                QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
                QPushButton:hover { background-color: #303f9f; }
                """
            )

    def update_attendance_table(self):
        self.daily_table.setRowCount(0)
        emp_code = self.session.get("employee_id", None)
        for entry in self.attendance_data:
            if self.is_admin or (emp_code and entry[0][0] == str(emp_code)):
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
        """Show glowing background flash instead of border"""
        self.camera_container.setStyleSheet(
            "QFrame { background: transparent; border: none; border-radius: 200px; }"
        )
        glow = QGraphicsDropShadowEffect(self.camera_container)
        glow.setOffset(0, 0)   # Glow centered
        glow.setBlurRadius(40) # Glow softness
        if recognition_status == "recognized":
            color = QColor("#4caf50")  # Green glow
        elif recognition_status == "detecting":
            color = QColor("#ff9800")  # Orange glow
        elif recognition_status == "failed":
            color = QColor("#f44336")  # Red glow
        else:
            color = QColor("#3f51b5")  # Blue glow (default flash from start)
        glow.setColor(color)
        self.camera_container.setGraphicsEffect(glow)
        self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
        self.glow_animation.setStartValue(20)
        self.glow_animation.setEndValue(80)
        self.glow_animation.setDuration(1000)   # 1 sec
        self.glow_animation.setLoopCount(-1)    # infinite
        self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.glow_animation.start()

    def reset_camera_border_after_delay(self):
        """Reset camera border to default after 3 seconds"""
        QTimer.singleShot(3000, lambda: self.update_camera_border("default"))

    def on_recognition_success(self, employee_name):
        """Called when face recognition is successful"""
        self.employee_card.update_value(employee_name)
        self.update_camera_border("recognized")
        self.reset_camera_border_after_delay()
        print(f"Recognition successful: {employee_name}")

    def on_recognition_failed(self):
        """Called when face recognition fails"""
        self.employee_card.update_value("Unknown Person")
        self.update_camera_border("failed")
        self.reset_camera_border_after_delay()
        print("Recognition failed")

    def on_detection_started(self):
        """Called when detection starts"""
        self.update_camera_border("detecting")
        print("Detection started")

    def on_detection_stopped(self):
        """Called when detection stops"""
        self.update_camera_border("default")
        print("Detection stopped")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = Sidebar(self.session)
        self.sidebar.date_selected.connect(self.update_table_by_date)
        main_layout.addWidget(self.sidebar)

        # Main content
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f5f5;")
        main_content_layout = QVBoxLayout(content_widget)
        main_content_layout.setSpacing(8)
        main_content_layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header_card = ModernCard()
        header_card.setFixedHeight(80)
        header_card.setStyleSheet(
            """
            QFrame { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; }
        """
        )
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(0, 2, 0, 0)
        header_layout.setSpacing(16)

        header_title = QLabel("Face Recognition Attendance System")
        header_title.setStyleSheet(
            "font-size: 22px; font-weight: 600; color: #ff9800; background: transparent;"
        )

        # Admin Login Button
        self.admin_login_btn = QPushButton("Admin Login")
        self.admin_login_btn.setCursor(Qt.PointingHandCursor)
        self.admin_login_btn.setFixedHeight(32)
        self.admin_login_btn.setStyleSheet(
            """
            QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
            QPushButton:hover { background-color: #303f9f; }
        """
        )
        self.admin_login_btn.clicked.connect(self.admin_login)

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet(
            """
            QPushButton { font-size: 13px; font-weight: 500; color: white; background-color: #f44336; border: none; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #d32f2f; }
        """
        )
        logout_btn.clicked.connect(self.logout)

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.admin_login_btn)
        header_layout.addWidget(logout_btn)

        main_content_layout.addWidget(header_card)

        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)

        # Left panel (Face Detection)
        left_panel = QFrame()
        left_panel.setFixedWidth(500)  # Reduced from 600 to 500
        left_panel.setStyleSheet(
            """
            QFrame { background-color: #ffffff; border: none; }
        """
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 2, 8, 8)
        left_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)

        self.live_dot = QLabel()
        self.live_dot.setFixedSize(24, 24)
        self.live_dot.setStyleSheet(
            """
            QLabel {
                background-color: #4caf50;
                border-radius: 12px;
                border: 3px solid #a5d6a7;
            }
        """
        )
        self.live_label = QLabel("Live")
        self.live_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 600;
            color: #212121;
            border: none;
            margin-top: 2px;
        """
        )
        self.live_label.setAlignment(Qt.AlignVCenter)

        live_header = QHBoxLayout()
        live_header.setContentsMargins(0, 0, 0, 0)
        live_header.setSpacing(6)
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
        self.employee_card.setFixedWidth(200)  # Reduced from 250 to 200
        header_row.addLayout(live_header)
        header_row.addStretch()
        header_row.addWidget(self.employee_card)
        left_layout.addLayout(header_row)
        left_layout.addSpacing(20)

        self.camera_container = QFrame()
        self.camera_container.setFixedSize(350, 350)  # Reduced from 420x420 to 350x350
        self.camera_container.setStyleSheet(
            "QFrame { background: transparent; border: 2px solid #3f51b5; border-radius: 175px; }"
        )
        camera_layout = QVBoxLayout(self.camera_container)
        camera_layout.setContentsMargins(10, 10, 10, 10)
        self.video_label = QLabel("Waiting for iVCam connection")
        self.video_label.setFixedSize(330, 330)  # Reduced from 400x400 to 330x330
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setWordWrap(True)
        self.video_label.setStyleSheet(
            "QLabel { background-color: transparent; border: none; }"
        )
        # Apply circular mask to video_label
        self.video_label.setMask(self.create_circular_mask(330, 330))  # Updated mask size
        camera_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.camera_container, alignment=Qt.AlignCenter)
        left_layout.addSpacing(10)

        self.device_info_data = get_device_info()
        self.device_info_label = QLabel(
            f"Device Name: {self.device_info_data['device_name']}\n"
            f"Device Model: {self.device_info_data['device_model']}\n"
            f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
            f"Internet Status: {self.device_info_data.get('internet_status','Unknown')}"
        )
        self.device_info_label.setStyleSheet(
            "font-size: 14px; font-weight: 500; color: #212121; border: none; margin-top: 5px;"
        )
        self.device_info_label.setWordWrap(True)
        left_layout.addWidget(self.device_info_label)
        left_layout.addSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("Start Detection")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(48)
        self.start_btn.setStyleSheet(
            """
            QPushButton { 
                font-size: 14px; 
                font-weight: 500; 
                color: white; 
                background: #4caf50; 
                border: none; 
                border-radius: 4px; 
                padding: 12px 24px; 
                margin-right: 5px;
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
        reset_btn.setFixedHeight(48)
        reset_btn.setStyleSheet(
            """
            QPushButton { 
                font-size: 14px; 
                font-weight: 500; 
                color: #757575; 
                background-color: #ffffff; 
                border: 1px solid #e0e0e0; 
                border-radius: 4px; 
                padding: 12px 24px;
                margin-left: 5px;
            }
            QPushButton:hover { background-color: #f5f5f5; border: 1px solid #bdbdbd; color: #424242; }
            QPushButton:pressed { background-color: #eeeeee; }
        """
        )
        button_layout.addWidget(self.start_btn, 2)
        button_layout.addWidget(reset_btn, 1)
        left_layout.addLayout(button_layout)

        content_layout.addWidget(left_panel)

        # Right panel (Overview cards and Daily Attendance Log)
        self.right_panel = ModernCard()
        self.right_panel.setStyleSheet(
            """
            QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
        """
        )
        self.right_panel.setVisible(False)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(14)

        top_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_lbl = QLabel("Offline Attendance")
        title_lbl.setStyleSheet(
            """
            font-size: 20px; 
            font-weight: 700;
            color: #212121;
            background: transparent;
            border: none;
        """
        )
        subtitle_lbl = QLabel("Overview")
        subtitle_lbl.setStyleSheet(
            """
            font-size: 12px;
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
        dt_row.setSpacing(8)
        dt_row.setContentsMargins(0, 0, 0, 0)
        self.date_label = QLabel("--- --- --")
        self.date_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 500;
            color: #1565c0;
            background: transparent;
            border: none;
        """
        )
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet(
            """
            font-size: 16px;
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

        overview_grid = QGridLayout()
        overview_grid.setHorizontalSpacing(12)
        overview_grid.setVerticalSpacing(12)

        def make_overview_card(title, number, sub, bg, fg, icon_text, compact=False):
            card = QFrame()
            card.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {bg};
                    border: none;
                    border-radius: 12px;
                }}
            """
            )
            v = QVBoxLayout(card)
            v.setContentsMargins(14, 14, 14, 14)
            v.setSpacing(6)
            icon = QLabel(icon_text)
            icon.setAlignment(Qt.AlignCenter)
            icon.setFixedSize(32, 32)
            icon.setStyleSheet(
                f"""
                QLabel {{
                    background: rgba(255,255,255,0.5);
                    border-radius: 16px;
                    font-size: 16px;
                    color: {fg};
                    font-weight: 700;
                }}
            """
            )
            if compact:
                t = QLabel(title)
                t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
                n = QLabel(str(number))
                n.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 500;")
                s = QLabel(sub)
                s.setStyleSheet(f"font-size: 11px; color: {fg};")
            else:
                t = QLabel(title)
                t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
                n = QLabel(str(number))
                n.setStyleSheet(f"font-size: 22px; color: {fg}; font-weight: 800;")
                s = QLabel(sub)
                s.setStyleSheet(f"font-size: 11px; color: {fg};")
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

        summary = get_daily_attendance_summary()
        total_emp = get_employee_count()
        present_today = summary["checked_in_only"] + summary["completed_attendance"]
        overview_grid.addWidget(
            make_overview_card(
                "Total Employees",
                str(total_emp),
                "All active staff members",
                "#E3F2FD",
                "#1E88E5",
                "👥",
            ),
            0,
            0,
        )
        overview_grid.addWidget(
            make_overview_card(
                "Present Today",
                str(present_today),
                "Checked-in employees",
                "#E8F5E9",
                "#2E7D32",
                "✅",
            ),
            0,
            1,
        )
        overview_grid.addWidget(
            make_overview_card(
                "Last DB Sync",
                "No. of Log =1560\nSynchronized =1560\nSync. Date =14-Aug-2025 at 11:06\nNo. of Failed logs: 0",
                "",
                "#FFF8E1",
                "#FF8C00",
                "🗄️",
                compact=True,
            ),
            0,
            2,
        )
        overview_grid.addWidget(
            make_overview_card(
                "Next Sync",
                "Scheduled for 20-Aug-2025 at 23:45",
                "",
                "#FCE4EC",
                "#D81B60",
                "⏳",
                compact=True,
            ),
            0,
            3,
        )
        right_layout.addLayout(overview_grid)

        section1_header = QHBoxLayout()
        title_alert_layout = QHBoxLayout()
        title_alert_layout.setSpacing(12)
        s1_title = QLabel("Daily Attendance Log")
        s1_title.setStyleSheet(
            """
            font-size: 20px;
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
        alert_layout.setSpacing(6)
        alert_icon = QLabel("⚠️")
        alert_icon.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                color: #FF8C00;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """
        )
        pending_sync_count = 8
        alert_msg = QLabel(f"{pending_sync_count} records pending sync")
        alert_msg.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #FF8C00;
                background: transparent;
                border: none;
                padding: 0px;
                font-weight: 500;
            }
        """
        )
        alert_layout.addWidget(alert_icon)
        alert_layout.addWidget(alert_msg)
        title_alert_layout.addWidget(alert_container)
        section1_header.addLayout(title_alert_layout)
        section1_header.addStretch()

        search_container = QWidget()
        search_container.setFixedWidth(220)
        search_container.setStyleSheet(
            """
            QWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #ffffff;
            }
            QWidget:focus-within {
                border-color: #bdbdbd;
            }
        """
        )
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 0, 8, 0)
        search_layout.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search employee...")
        self.search_input.setStyleSheet(
            """
            QLineEdit { 
                border: none;
                background: transparent;
                font-size: 13px;
                padding: 8px 0px;
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
                font-size: 14px;
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
        self.daily_table.setStyleSheet(
            """
            QTableWidget { 
                background-color: #ffffff; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                font-size: 14px; 
                color: #424242; 
                gridline-color: #eeeeee; 
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item { 
                padding: 12px 16px; 
                border-bottom: 1px solid #eeeeee; 
                border-right: none; 
            }
            QTableWidget::item:selected { 
                background-color: #e3f2fd; 
                color: #0d47a1; 
                font-weight: 500; 
            }
            QTableWidget::item:alternate { 
                background-color: #fafafa; 
            }
            QHeaderView::section { 
                background: #001F3F; 
                color: #ffffff; 
                font-weight: 500; 
                font-size: 13px; 
                padding: 12px 16px; 
                border: none; 
                text-transform: uppercase; 
            }
            QScrollBar:vertical { 
                background-color: #001F3F; 
                width: 10px; 
                border-radius: 4px; 
            }
            QScrollBar::handle:vertical { 
                background-color: #bdbdbd; 
                border-radius: 4px; 
                min-height: 20px; 
            }
            QScrollBar::handle:vertical:hover { 
                background-color: #9e9e9e; 
            }
            QScrollBar::add-line:vertical { 
                background: #001F3F;
                height: 15px;
                border-radius: 4px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical { 
                background: #001F3F;
                height: 15px;
                border-radius: 4px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover { 
                background: #303f9f;
            }
            QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed { 
                background: #1a237e;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 5px;
                height: 5px;
                background: white;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        )
        self.daily_table.setMinimumHeight(500)
        self.daily_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.daily_table)
        right_layout.addItem(
            QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        content_layout.addWidget(self.right_panel, 2)
        main_content_layout.addLayout(content_layout)
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
        self.is_detecting = False
        self.update_time()

    def update_time(self):
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%I:%M:%S"))
        self.date_label.setText(now.strftime("%B %d, %Y"))

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
                QPushButton { font-size: 14px; font-weight: 500; color: white; background: #4caf50; border: none; border-radius: 4px; padding: 12px 24px; }
                QPushButton:hover { background: #388e3c; }
            """
            )
            print("Detection stopped")
        else:
            self.detect_timer.start(1000)
            self.start_btn.setText("Stop Detection")
            self.start_btn.setStyleSheet(
                """
                QPushButton { font-size: 14px; font-weight: 500; color: white; background: #f44336; border: none; border-radius: 4px; padding: 12px 24px; }
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
                self.load_attendance_logs()
                name = result.get("emp_full_name", "Employee")
                self.employee_card.update_value(name)
                self.update_camera_border("recognized")
                self.reset_camera_border_after_delay()
                speak("Hello " + name)
                self.daily_table.scrollToTop()
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
        logs = get_attendance_logs()
        self.daily_table.setRowCount(0)
        if hasattr(self, "selected_date_label"):
            self.selected_date_label.setText(
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
                log.get("mode", "FACE"),
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                if col == 5:
                    if text == "CHECKED_IN":
                        item = QTableWidgetItem("MSP")
                        item.setForeground(QColor("yellow"))
                    elif text == "CHECKED_OUT":
                        item = QTableWidgetItem("Present")
                        item.setForeground(QColor("green"))
                    else:
                        item.setForeground(QColor("blue"))
                item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.daily_table.setItem(row_pos, col, item)
        self.daily_table.scrollToTop()

    def update_table_by_date(self, selected_date):
        logs = get_attendance_by_date(selected_date)
        if hasattr(self, "selected_date_label"):
            self.selected_date_label.setText(
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
                    log.get("mode", "FACE"),
                ]
                for col, text in enumerate(row_data):
                    item = QTableWidgetItem(text)
                    if col == 5:
                        if text == "CHECKED_IN":
                            item = QTableWidgetItem("MSP")
                            item.setForeground(QColor("yellow"))
                        elif text == "CHECKED_OUT":
                            item = QTableWidgetItem("Present")
                            item.setForeground(QColor("green"))
                        else:
                            item.setForeground(QColor("blue"))
                    item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    self.daily_table.setItem(row_pos, col, item)
            self.daily_table.scrollToTop()
        else:
            print(f"No attendance found for {selected_date}")

def run_app():
    app = QApplication(sys.argv)
    init_db()
    # Load session if available, else use default
    session = load_session() if is_logged_in() else {"name": "Guest", "role": "Employee"}
    window = AttendanceApp(session)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()

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
# )

# # --- Your existing helpers (unchanged) ---
# from fetch_emp_from_fixhr import fetch_and_store_employees
# from login import login_fixhr, is_logged_in, load_session, clear_session
# from database import (
#     get_attendance_logs,
#     get_daily_attendance_summary,
#     get_employee_count,
#     get_attendance_by_date,
#     init_db,
# )
# from device_info import get_device_info, is_internet_available
# from speak import speak
# from backup_utils import BackupManager
# import io

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# # ---------------------- Date Format Helpers ----------------------
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

# # ---------------------- Threads ----------------------
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

# # ---------------------- UI Helpers ----------------------
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
#         self.setFixedHeight(80)
#         self.setStyleSheet(
#             f"""
#             QFrame {{
#                 border-left: 4px solid {color};
#                 border-radius: 6px;
#                 padding: 12px;
#                 margin: 4px;
#             }}
#             QFrame:hover {{
#             }}
#         """
#         )
#         layout = QVBoxLayout(self)
#         layout.setSpacing(6)
#         layout.setContentsMargins(8, 8, 8, 8)
#         title_label = QLabel(title)
#         title_label.setStyleSheet(
#             """
#             font-size: 13px; font-weight: 500; color: #757575; background: transparent;
#         """
#         )
#         self.value_label = QLabel(value)
#         self.value_label.setStyleSheet(
#             """
#             font-size: 15px; font-weight: 600; color: #212121; background: transparent;
#         """
#         )
#         layout.addWidget(title_label)
#         layout.addWidget(self.value_label)

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
#         painter.save()
#         center = rect.center()
#         radius = min(rect.width(), rect.height()) // 2 - 6
#         accent = QColor("#0078D7")
#         if is_today and not is_selected:
#             painter.setBrush(QBrush(accent))
#             painter.setPen(Qt.NoPen)
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         elif is_selected:
#             painter.setBrush(Qt.NoBrush)
#             painter.setPen(QPen(accent, 2))
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         elif is_hovered:
#             painter.setBrush(QBrush(QColor(0, 120, 215, 80)))
#             painter.setPen(Qt.NoPen)
#             painter.drawEllipse(center, radius, radius)
#             painter.setPen(Qt.white)
#         else:
#             painter.setPen(Qt.white)
#         painter.drawText(rect, Qt.AlignCenter, text)
#         painter.restore()

# def get_app_version():
#     try:
#         return importlib.metadata.version("FixHR")
#     except importlib.metadata.PackageNotFoundError:
#         return "dev"

# # ---------------- SIDEBAR CLASS ----------------
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

#         self.logo_label = QLabel("FixHR")
#         self.logo_label.setStyleSheet(
#             "font-size: 20px; font-weight: 700; color: #FF8C00; background: transparent;"
#         )
#         self.logo_label.setAlignment(Qt.AlignLeft)

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

#         user_avatar = QLabel("👤")
#         user_avatar.setStyleSheet(
#             """
#             font-size: 60px;
#             background-color: #002F5E;
#             border-radius: 40px;
#             padding: 8px;
#             color: #F5F5F5;
#             border: 2px solid #004080;
#             box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
#             """
#         )
#         user_avatar.setFixedSize(80, 80)
#         user_avatar.setAlignment(Qt.AlignCenter)

#         user_name = QLabel(f"Welcome, {self.session.get('name','User')}")
#         user_name.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent;")
#         user_name.setAlignment(Qt.AlignCenter)

#         user_role = QLabel(self.session.get("role", "Employee"))
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

#         self.fetch_btn = QPushButton("Fetch Employees")
#         self.fetch_btn.setCursor(Qt.PointingHandCursor)
#         self.fetch_btn.setStyleSheet(
#             """
#             QPushButton {
#                 background-color: #002F5E;
#                 color: white;
#                 border: none;
#                 padding: 6px 10px;
#                 border-radius: 5px;
#             }
#             QPushButton:hover {
#                 background-color: #004080;
#             }
#         """
#         )
#         self.fetch_btn.clicked.connect(lambda: self.parent().fetch_employees())
#         layout.addWidget(self.fetch_btn, alignment=Qt.AlignLeft)

#         layout.addStretch()

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
#             """
#         )
#         self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
#         self.calendar.selectionChanged.connect(self.on_date_selected)

#         view = self.calendar.findChild(QTableView)
#         if view:
#             view.setItemDelegate(CalendarDelegate(view))

#         layout.addWidget(self.calendar, alignment=Qt.AlignLeft)

#         main_layout.addWidget(scroll)

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
#             self.cal_label.show()
#             self.calendar.show()
#             self.fetch_btn.show()
#             self.is_collapsed = False
#         else:
#             self.setFixedWidth(self.collapsed_width)
#             self.toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
#             self.logo_label.hide()
#             self.version_label.hide()
#             self.nav_label.hide()
#             self.cal_label.hide()
#             self.calendar.hide()
#             self.fetch_btn.hide()
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

# # ---------------------- Main App ----------------------
# class AttendanceApp(QWidget):
#     def __init__(self, session=None):
#         super().__init__()
#         self.session = session or {"name": "Guest", "role": "Employee"}
#         self.setWindowTitle("FixHR - Face Recognition Attendance System")
#         self.setGeometry(50, 50, 1800, 1000)
#         self.setStyleSheet(
#             """
#             QWidget { background-color: #001F3F; font-family: 'Segoe UI','Roboto',sans-serif; color: #ffffff; }
#         """
#         )
#         self.setWindowIcon(QIcon("C:/Users/Kesar/Documents/GitHub/Offline-Face-Recognition/fix_hr_prod_logo.png"))
#         self.liveness_detector_loaded = False
#         self.detect_and_predict = None
#         self.fetch_thread = None
#         self.liveness_loader_thread = None
#         self.detect_worker_running = False
#         self._detect_worker = None
#         self.is_admin = False
#         self.attendance_data = []
#         self.cap = None
#         self.init_ui()
#         self.init_timers()
#         self.load_liveness_detector_async()
#         self.backup_manager = BackupManager(
#             db_path="C:/Users/Kesar/Documents/GitHub/Offline-Face-Recognition/employees.db",
#         )
#         self.backup_manager.start()

#     def create_circular_mask(self, width, height):
#         """Create a circular QRegion for masking the video_label"""
#         region = QRegion(0, 0, width, height, QRegion.Ellipse)
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
#         self.sidebar.fetch_btn.setEnabled(True)
#         self.sidebar.fetch_btn.setText("Fetch Employees")
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
#             # Clear session data
#             clear_session()
            
#             # Reset admin state
#             self.is_admin = False
            
#             # Hide right panel (admin view)
#             self.right_panel.setVisible(False)
            
#             # Reset session to guest
#             self.session = {"name": "Guest", "role": "Employee"}
            
#             # Create new sidebar with guest session
#             new_sidebar = Sidebar(self.session)
#             new_sidebar.date_selected.connect(self.update_table_by_date)
            
#             # Replace the current sidebar with the new one
#             main_layout = self.layout()
#             old_sidebar = main_layout.itemAt(0).widget()
#             main_layout.replaceWidget(old_sidebar, new_sidebar)
#             old_sidebar.deleteLater()  # Clean up old sidebar
#             self.sidebar = new_sidebar
            
#             # Reset admin login button
#             self.admin_login_btn.setText("Admin Login")
#             self.admin_login_btn.setStyleSheet(
#                 """
#                 QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
#                 QPushButton:hover { background-color: #303f9f; }
#             """
#             )
            
#             # Reset employee card
#             self.employee_card.update_value("[Employee Name]")
            
#             # Show success message
#             QMessageBox.information(self, "Success", "Successfully logged out!")
            
#             print("Logged out successfully - showing guest view with sidebar and face detection")

#     def admin_login(self):
#         # Check if already logged in
#         if is_logged_in():
#             reply = QMessageBox.question(
#                 self,
#                 "Session Active",
#                 "An admin session is already active. Do you want to log out the current session and log in again?",
#                 QMessageBox.Yes | QMessageBox.No,
#                 QMessageBox.No,
#             )
#             if reply == QMessageBox.Yes:
#                 clear_session()  # Clear existing session
#                 self.session = {"name": "Guest", "role": "Employee"}  # Reset to guest
#                 self.is_admin = False
#                 self.right_panel.setVisible(False)
#                 # Update sidebar to reflect guest state
#                 new_sidebar = Sidebar(self.session)
#                 new_sidebar.date_selected.connect(self.update_table_by_date)
#                 self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
#                 self.sidebar = new_sidebar
#             else:
#                 return  # Exit if user chooses not to log out

#         # Show login dialog
#         dialog = LoginDialog()
#         if dialog.exec_() == QDialog.Accepted:
#             email, password = dialog.get_credentials()
#             result = login_fixhr(email, password)
#             if result["status"] == "success":
#                 self.session = result["data"]
#                 self.is_admin = True
#                 self.right_panel.setVisible(True)  # Show four-box overview and attendance table
#                 self.load_attendance_logs()  # Populate daily attendance table
#                 self.admin_login_btn.setText("Admin: Logged In")
#                 self.admin_login_btn.setStyleSheet(
#                     """
#                     QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #4caf50; border: none; border-radius: 4px; padding: 8px 16px; }
#                     QPushButton:hover { background-color: #388e3c; }
#                     """
#                 )
#                 # Update sidebar with new session data
#                 new_sidebar = Sidebar(self.session)
#                 new_sidebar.date_selected.connect(self.update_table_by_date)
#                 self.layout().replaceWidget(self.layout().itemAt(0).widget(), new_sidebar)
#                 self.sidebar = new_sidebar
#                 QMessageBox.information(self, "Success", "Admin login successful")
#                 print("Admin logged in - showing right panel with four-box overview and daily attendance")
#             else:
#                 self.is_admin = False
#                 self.right_panel.setVisible(False)
#                 QMessageBox.critical(
#                     self, "Login Failed", result.get("message", "Unknown error")
#                 )
#         else:
#             self.is_admin = False
#             self.right_panel.setVisible(False)
#             self.admin_login_btn.setText("Admin Login")
#             self.admin_login_btn.setStyleSheet(
#                 """
#                 QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
#                 QPushButton:hover { background-color: #303f9f; }
#                 """
#             )

#     def update_attendance_table(self, data):
#         self.daily_table.setRowCount(0)
#         emp_code = self.session.get("employee_id", None)
#         for entry in data:
#             if self.is_admin or (emp_code and entry[0][0] == str(emp_code)):
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
#         """Show glowing background flash instead of border"""
#         self.camera_container.setStyleSheet(
#             "QFrame { background: transparent; border: none; border-radius: 210px; }"
#         )
#         glow = QGraphicsDropShadowEffect(self.camera_container)
#         glow.setOffset(0, 0)   # Glow centered
#         glow.setBlurRadius(40) # Glow softness
#         if recognition_status == "recognized":
#             color = QColor("#4caf50")  # Green glow
#         elif recognition_status == "detecting":
#             color = QColor("#ff9800")  # Orange glow
#         elif recognition_status == "failed":
#             color = QColor("#f44336")  # Red glow
#         else:
#             color = QColor("#3f51b5")  # Blue glow (default flash from start)
#         glow.setColor(color)
#         self.camera_container.setGraphicsEffect(glow)
#         self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
#         self.glow_animation.setStartValue(20)
#         self.glow_animation.setEndValue(80)
#         self.glow_animation.setDuration(1000)   # 1 sec
#         self.glow_animation.setLoopCount(-1)    # infinite
#         self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
#         self.glow_animation.start()

#     def reset_camera_border_after_delay(self):
#         """Reset camera border to default after 3 seconds"""
#         QTimer.singleShot(3000, lambda: self.update_camera_border("default"))

#     def on_recognition_success(self, employee_name):
#         """Called when face recognition is successful"""
#         self.employee_card.update_value(employee_name)
#         self.update_camera_border("recognized")
#         self.reset_camera_border_after_delay()
#         print(f"Recognition successful: {employee_name}")

#     def on_recognition_failed(self):
#         """Called when face recognition fails"""
#         self.employee_card.update_value("Unknown Person")
#         self.update_camera_border("failed")
#         self.reset_camera_border_after_delay()
#         print("Recognition failed")

#     def on_detection_started(self):
#         """Called when detection starts"""
#         self.update_camera_border("detecting")
#         print("Detection started")

#     def on_detection_stopped(self):
#         """Called when detection stops"""
#         self.update_camera_border("default")
#         print("Detection stopped")

#     def init_ui(self):
#         main_layout = QHBoxLayout(self)
#         main_layout.setSpacing(0)
#         main_layout.setContentsMargins(0, 0, 0, 0)

#         # Sidebar
#         self.sidebar = Sidebar(self.session)
#         self.sidebar.date_selected.connect(self.update_table_by_date)
#         main_layout.addWidget(self.sidebar)

#         # Main content
#         content_widget = QWidget()
#         content_widget.setStyleSheet("background-color: #f5f5f5;")
#         main_content_layout = QVBoxLayout(content_widget)
#         main_content_layout.setSpacing(8)
#         main_content_layout.setContentsMargins(12, 12, 12, 12)

#         # Header
#         header_card = ModernCard()
#         header_card.setFixedHeight(80)
#         header_card.setStyleSheet(
#             """
#             QFrame { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; }
#         """
#         )
#         header_layout = QHBoxLayout(header_card)
#         header_layout.setContentsMargins(0, 2, 0, 0)
#         header_layout.setSpacing(16)

#         header_title = QLabel("Face Recognition Attendance System")
#         header_title.setStyleSheet(
#             "font-size: 22px; font-weight: 600; color: #ff9800; background: transparent;"
#         )

#         # Admin Login Button
#         self.admin_login_btn = QPushButton("Admin Login")
#         self.admin_login_btn.setCursor(Qt.PointingHandCursor)
#         self.admin_login_btn.setFixedHeight(32)
#         self.admin_login_btn.setStyleSheet(
#             """
#             QPushButton { font-size: 13px; font-weight: 500; color: #ffffff; background-color: #3f51b5; border: none; border-radius: 4px; padding: 8px 16px; }
#             QPushButton:hover { background-color: #303f9f; }
#         """
#         )
#         self.admin_login_btn.clicked.connect(self.admin_login)

#         logout_btn = QPushButton("Logout")
#         logout_btn.setCursor(Qt.PointingHandCursor)
#         logout_btn.setFixedHeight(32)
#         logout_btn.setStyleSheet(
#             """
#             QPushButton { font-size: 13px; font-weight: 500; color: white; background-color: #f44336; border: none; border-radius: 4px; padding: 6px 12px; }
#             QPushButton:hover { background-color: #d32f2f; }
#         """
#         )
#         logout_btn.clicked.connect(self.logout)

#         header_layout.addWidget(header_title)
#         header_layout.addStretch()
#         header_layout.addWidget(self.admin_login_btn)
#         header_layout.addWidget(logout_btn)

#         main_content_layout.addWidget(header_card)

#         # Content layout
#         content_layout = QHBoxLayout()
#         content_layout.setSpacing(8)

#         # Left panel (Face Detection - Vertical Layout)
#         left_panel = QFrame()
#         left_panel.setFixedWidth(1000)  # Increased width for larger white box
#         left_panel.setStyleSheet(
#             """
#             QFrame { background-color: #ffffff; border: none; }
#         """
#         )
#         left_layout = QVBoxLayout(left_panel)
#         left_layout.setContentsMargins(20, 20, 20, 20)  # Increased margins for spacing
#         left_layout.setSpacing(20)  # Increased spacing for better separation

#         # Header row (Live status and Employee card)
#         header_row = QHBoxLayout()
#         header_row.setContentsMargins(0, 0, 0, 0)
#         header_row.setSpacing(12)

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
#             margin-top: 2px;
#         """
#         )
#         self.live_label.setAlignment(Qt.AlignVCenter)
#         header_row.addWidget(self.live_dot, 0, Qt.AlignVCenter)
#         header_row.addWidget(self.live_label, 0, Qt.AlignVCenter)

#         self.blink_state = True
#         self.online_status = True
#         self.blink_timer = QTimer()
#         self.blink_timer.timeout.connect(self.toggle_blink)
#         self.blink_timer.start(600)
#         self.internet_timer = QTimer()
#         self.internet_timer.timeout.connect(self.update_internet_status)
#         self.internet_timer.start(5000)

#         self.employee_card = StatusCard("Employee", "[Employee Name]", "#4caf50")
#         self.employee_card.setFixedWidth(350)  # Increased width for balance
#         header_row.addWidget(self.employee_card)

#         left_layout.addLayout(header_row)

#         # Camera Container
#         self.camera_container = QFrame()
#         self.camera_container.setFixedSize(420, 420)
#         self.camera_container.setStyleSheet(
#             "QFrame { background: transparent; border: 2px solid #3f51b5; border-radius: 210px; }"
#         )
#         camera_layout = QVBoxLayout(self.camera_container)
#         camera_layout.setContentsMargins(10, 10, 10, 10)
#         self.video_label = QLabel("Waiting for iVCam connection")
#         self.video_label.setFixedSize(400, 400)
#         self.video_label.setAlignment(Qt.AlignCenter)
#         self.video_label.setWordWrap(True)
#         self.video_label.setStyleSheet(
#             "QLabel { background-color: transparent; border: none; }"
#         )
#         self.video_label.setMask(self.create_circular_mask(400, 400))
#         camera_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
#         left_layout.addWidget(self.camera_container, alignment=Qt.AlignCenter)

#         # Device Info
#         self.device_info_data = get_device_info()
#         self.device_info_label = QLabel(
#             f"Device Name: {self.device_info_data['device_name']}\n"
#             f"Device Model: {self.device_info_data['device_model']}\n"
#             f"Connectivity Mode: {self.device_info_data['connectivity']}\n"
#             f"Internet Status: {self.device_info_data.get('internet_status','Unknown')}"
#         )
#         self.device_info_label.setStyleSheet(
#             "font-size: 14px; font-weight: 500; color: #212121; border: none;"
#         )
#         self.device_info_label.setWordWrap(True)
#         self.device_info_label.setFixedWidth(350)  # Increased width for balance
#         left_layout.addWidget(self.device_info_label, alignment=Qt.AlignCenter)

#         # Buttons
#         button_layout = QHBoxLayout()
#         button_layout.setContentsMargins(0, 0, 0, 0)
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
#             }
#             QPushButton:hover { background-color: #f5f5f5; border: 1px solid #bdbdbd; color: #424242; }
#             QPushButton:pressed { background-color: #eeeeee; }
#         """
#         )
#         button_layout.addWidget(self.start_btn)
#         button_layout.addWidget(reset_btn)
#         left_layout.addLayout(button_layout)

#         content_layout.addWidget(left_panel)

#         # Right panel (Overview cards and Daily Attendance Log)
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
#         self.date_label = QLabel("--- --- --")
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

#         overview_grid = QGridLayout()
#         overview_grid.setHorizontalSpacing(12)
#         overview_grid.setVerticalSpacing(12)

#         def make_overview_card(title, number, sub, bg, fg, icon_text, compact=False):
#             card = QFrame()
#             card.setStyleSheet(
#                 f"""
#                 QFrame {{
#                     background-color: {bg};
#                     border: none;
#                     border-radius: 12px;
#                 }}
#             """
#             )
#             v = QVBoxLayout(card)
#             v.setContentsMargins(14, 14, 14, 14)
#             v.setSpacing(6)
#             icon = QLabel(icon_text)
#             icon.setAlignment(Qt.AlignCenter)
#             icon.setFixedSize(32, 32)
#             icon.setStyleSheet(
#                 f"""
#                 QLabel {{
#                     background: rgba(255,255,255,0.5);
#                     border-radius: 16px;
#                     font-size: 16px;
#                     color: {fg};
#                     font-weight: 700;
#                 }}
#             """
#             )
#             if compact:
#                 t = QLabel(title)
#                 t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
#                 n = QLabel(str(number))
#                 n.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 500;")
#                 s = QLabel(sub)
#                 s.setStyleSheet(f"font-size: 11px; color: {fg};")
#             else:
#                 t = QLabel(title)
#                 t.setStyleSheet(f"font-size: 12px; color: {fg}; font-weight: 600;")
#                 n = QLabel(str(number))
#                 n.setStyleSheet(f"font-size: 22px; color: {fg}; font-weight: 800;")
#                 s = QLabel(sub)
#                 s.setStyleSheet(f"font-size: 11px; color: {fg};")
#                 t.setWordWrap(True)
#                 n.setWordWrap(True)
#                 s.setWordWrap(True)
#             top_h = QHBoxLayout()
#             top_h.setSpacing(8)
#             top_h.addWidget(icon, 0, Qt.AlignLeft)
#             top_h.addWidget(t, 0, Qt.AlignVCenter)
#             top_h.addStretch()
#             v.addLayout(top_h)
#             v.addWidget(n)
#             if sub:
#                 v.addWidget(s)
#             return card

#         summary = get_daily_attendance_summary()
#         total_emp = get_employee_count()
#         present_today = summary["checked_in_only"] + summary["completed_attendance"]
#         overview_grid.addWidget(
#             make_overview_card(
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
#         overview_grid.addWidget(
#             make_overview_card(
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
#         overview_grid.addWidget(
#             make_overview_card(
#                 "Last DB Sync",
#                 "No. of Log =1560\nSynchronized =1560\nSync. Date =14-Aug-2025 at 11:06\nNo. of Failed logs: 0",
#                 "",
#                 "#FFF8E1",
#                 "#FF8C00",
#                 "🗄️",
#                 compact=True,
#             ),
#             0,
#             2,
#         )
#         overview_grid.addWidget(
#             make_overview_card(
#                 "Next Sync",
#                 "Scheduled for 20-Aug-2025 at 23:45",
#                 "",
#                 "#FCE4EC",
#                 "#D81B60",
#                 "⏳",
#                 compact=True,
#             ),
#             0,
#             3,
#         )
#         right_layout.addLayout(overview_grid)

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
#         pending_sync_count = 8
#         alert_msg = QLabel(f"{pending_sync_count} records pending sync")
#         alert_msg.setStyleSheet(
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
#         alert_layout.addWidget(alert_msg)
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
#         self.daily_table.setStyleSheet(
#             """
#             QTableWidget { 
#                 background-color: #ffffff; 
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
#             QTableWidget::item:alternate { 
#                 background-color: #fafafa; 
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
#         """
#         )
#         self.daily_table.setMinimumHeight(500)
#         self.daily_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         right_layout.addWidget(self.daily_table)
#         right_layout.addItem(
#             QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
#         )

#         content_layout.addWidget(self.right_panel, 2)
#         main_content_layout.addLayout(content_layout)
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
#         self.is_detecting = False
#         self.update_time()

#     def update_time(self):
#         now = datetime.datetime.now()
#         self.time_label.setText(now.strftime("%I:%M:%S"))
#         self.date_label.setText(now.strftime("%B %d, %Y"))

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
#                 self.load_attendance_logs()
#                 name = result.get("emp_full_name", "Employee")
#                 self.employee_card.update_value(name)
#                 self.update_camera_border("recognized")
#                 self.reset_camera_border_after_delay()
#                 speak("Hello " + name)
#                 self.daily_table.scrollToTop()
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
#         logs = get_attendance_logs()
#         self.daily_table.setRowCount(0)
#         if hasattr(self, "selected_date_label"):
#             self.selected_date_label.setText(
#                 f"Date: {datetime.datetime.now().strftime('%d-%m-%y')}"
#             )
#         for log in logs:
#             row_pos = self.daily_table.rowCount()
#             self.daily_table.insertRow(row_pos)
#             row_data = [
#                 format_date_ddmmyy(log["checkin_date"]),
#                 str(log["emp_code"]),
#                 log["emp_full_name"],
#                 log["checkin_time"],
#                 log["checkout_time"] if log["checkout_time"] else "-",
#                 log["status"] if log["status"] else "Pending",
#                 log.get("mode", "FACE"),
#             ]
#             for col, text in enumerate(row_data):
#                 item = QTableWidgetItem(text)
#                 if col == 5:
#                     if text == "CHECKED_IN":
#                         item = QTableWidgetItem("MSP")
#                         item.setForeground(QColor("yellow"))
#                     elif text == "CHECKED_OUT":
#                         item = QTableWidgetItem("Present")
#                         item.setForeground(QColor("green"))
#                     else:
#                         item.setForeground(QColor("blue"))
#                 item.setFont(QFont("Segoe UI", 10, QFont.Bold))
#                 self.daily_table.setItem(row_pos, col, item)
#         self.daily_table.scrollToTop()

#     def update_table_by_date(self, selected_date):
#         logs = get_attendance_by_date(selected_date)
#         if hasattr(self, "selected_date_label"):
#             self.selected_date_label.setText(
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
#                     log.get("mode", "FACE"),
#                 ]
#                 for col, text in enumerate(row_data):
#                     item = QTableWidgetItem(text)
#                     if col == 5:
#                         if text == "CHECKED_IN":
#                             item = QTableWidgetItem("MSP")
#                             item.setForeground(QColor("yellow"))
#                         elif text == "CHECKED_OUT":
#                             item = QTableWidgetItem("Present")
#                             item.setForeground(QColor("green"))
#                         else:
#                             item.setForeground(QColor("blue"))
#                     item.setFont(QFont("Segoe UI", 10, QFont.Bold))
#                     self.daily_table.setItem(row_pos, col, item)
#             self.daily_table.scrollToTop()
#         else:
#             print(f"No attendance found for {selected_date}")

# def run_app():
#     app = QApplication(sys.argv)
#     init_db()
#     # Load session if available, else use default
#     session = load_session() if is_logged_in() else {"name": "Guest", "role": "Employee"}
#     window = AttendanceApp(session)
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     run_app()