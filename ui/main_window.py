import os
import sys
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QStatusBar, QFrame, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QFileSystemWatcher, QTimer
from PyQt5.QtGui import QFont, QIcon
from ui.batch_dialog import BatchDialog

# 프로젝트 루트 경로 추가 (필요 시)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 감시할 디렉토리 설정 (현재 폴더의 'watch' 폴더 예시)
        self.watch_path = os.path.join(os.getcwd(), "watch_folder")
        if not os.path.exists(self.watch_path):
            os.makedirs(self.watch_path)

        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        
        self.init_ui()

    # --- [추가] 이 함수가 있어야 아이콘 경로를 찾을 수 있습니다 ---
    def get_resource_path(self, relative_path):
        """ 실행 파일(.exe) 혹은 소스코드 환경에서 리소스의 절대 경로를 반환 """
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 환경 (임시 폴더 경로)
            base_path = sys._MEIPASS
        else:
            # 일반 파이썬 실행 환경 (현재 파일의 상위 폴더 기준)
            # ui/ 폴더 안에 있으므로 한 단계 더 위로 올라가야 assets를 찾습니다.
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.normpath(os.path.join(base_path, relative_path))

    def init_ui(self):

        icon_path = self.get_resource_path("assets/data/aztech_icon.ico")
    
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠️ 아이콘을 찾을 수 없음: {icon_path}")

        # 1. 기본 창 설정 (기존 600 -> 800으로 확장)
        self.setWindowTitle("🛠️ AZtech 자동화 시스템 v2.0")
        self.setFixedWidth(800) # 가로 길이를 800으로 고정
        self.setMinimumHeight(600) # 최소 높이 설정

        # 메인 위젯 및 레이아웃
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20) # 여백을 주어 더 깔끔하게
        layout.setSpacing(15)

        # 2. 상단: 유틸리티 버튼 구역
        top_bar = QHBoxLayout()
        self.btn_settings = QPushButton("⚙️ 설정")
        self.btn_settings.setFixedWidth(80)
        self.btn_settings.setStyleSheet("padding: 5px; font-weight: bold;")
        
        self.btn_help = QPushButton("❓ 도움말")
        self.btn_help.setFixedWidth(100)
        self.btn_help.setStyleSheet("padding: 5px; font-weight: bold;")
        
        top_bar.addWidget(self.btn_settings)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_help)
        layout.addLayout(top_bar)

        # 3. 중앙: 상태 표시 및 대형 감시 버튼
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        status_layout = QVBoxLayout(status_frame)

        self.lbl_status = QLabel("대기 중")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFont(QFont("Malgun Gothic", 14, QFont.Weight.Bold))
        self.lbl_status.setStyleSheet("color: #7f8c8d; border: none;")
        
        self.btn_toggle_watch = QPushButton("감시 시작")
        self.btn_toggle_watch.setFixedHeight(80)
        self.btn_toggle_watch.setFont(QFont("Malgun Gothic", 16, QFont.Weight.Bold))
        self.btn_toggle_watch.setStyleSheet("""
            background-color: #2ecc71; color: white; 
            border-radius: 10px; border: none;
        """)
        
        status_layout.addWidget(self.lbl_status)
        status_layout.addWidget(self.btn_toggle_watch)
        layout.addWidget(status_frame)

        # 4. 하단: 실시간 로그 창
        layout.addSpacing(10)
        layout.addWidget(QLabel("📝 작업 로그:"))
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            background-color: #1e1e1e; color: #d4d4d4; 
            font-family: Consolas; font-size: 10pt;
        """)
        layout.addWidget(self.log_viewer)

        # 5. 상태 표시줄
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("시스템 준비 완료")

        # 이벤트 연결
        self.btn_toggle_watch.clicked.connect(self.toggle_watcher)
        self.btn_help.clicked.connect(self.show_help)

        self.btn_batch_process = QPushButton("📂 일괄 엑셀 처리하기")
        self.btn_batch_process.setFixedHeight(40) # 버튼이 너무 작지 않게 높이 조절 (선택)
        self.btn_batch_process.setStyleSheet("font-weight: bold; background-color: #f1f2f6;")
        self.btn_batch_process.clicked.connect(self.open_batch_dialog)

        # 위에서 선언한 layout 변수를 그대로 사용합니다.
        layout.addWidget(self.btn_batch_process)

    # --- 기능 함수들 ---
    def open_batch_dialog(self):
        # self.parser는 메인 윈도우가 가지고 있는 PDF 파서 인스턴스입니다.
        # 만약 파서 이름이 다르면 사원님이 설정한 이름으로 바꿔주세요!
        self.batch_win = BatchDialog(self.parser, self) 
        
        # .exec_()를 사용하면 이 창이 떠 있는 동안은 메인 창을 건드릴 수 없습니다 (안전함)
        # .show()를 사용하면 메인 창과 동시에 조작할 수 있습니다.
        self.batch_win.exec_()


    def add_log(self, message, force_top=False):
        """로그 추가 및 조건에 따른 창 최상단 활성화"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {message}")
        self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

        if force_top:
            self.bring_to_front()

    def bring_to_front(self):
        """앱을 강제로 화면 최상단으로 호출"""
        # WindowStaysOnTopHint를 주면 다른 모든 창보다 위에 옵니다.
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.show()             # 창 보이기 (최소화 해제 포함)
        self.raise_()           # 상위 레이어로 올리기
        self.activateWindow()   # 포커스 강제 획득
        
        # 1.5초 후 '항상 위' 플래그만 제거하여 다른 작업 방해를 최소화함
        QTimer.singleShot(1500, self.release_top_hint)

    def release_top_hint(self):
        """항상 위 플래그 제거 (창 위치는 유지됨)"""
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def on_directory_changed(self, path):
        """폴더 내 파일 변화 감지 시 실행될 콜백"""
        self.add_log("🔔 [감지] 폴더 내 변화가 감지되었습니다!", force_top=True)

    def toggle_watcher(self):
        """감시 시작/중지 토글"""
        if self.btn_toggle_watch.text() == "감시 시작":
            self.watcher.addPath(self.watch_path) # 감시 시작
            self.btn_toggle_watch.setText("감시 중지")
            self.btn_toggle_watch.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 10px;")
            self.lbl_status.setText("🔍 실시간 감시 중...")
            self.lbl_status.setStyleSheet("color: #e74c3c; border: none;")
            self.add_log(f"🚀 감시 시작: {self.watch_path}")
        else:
            self.watcher.removePath(self.watch_path) # 감시 중단
            self.btn_toggle_watch.setText("감시 시작")
            self.btn_toggle_watch.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 10px;")
            self.lbl_status.setText("대기 중")
            self.lbl_status.setStyleSheet("color: #7f8c8d; border: none;")
            self.add_log("🛑 감시가 중단되었습니다.")

    def show_help(self):
        help_text = """
        <div style="font-family: 'Malgun Gothic'; line-height: 150%;">
            <h2 style="color: #2980b9;">🛠️ AZtech 자동화 시스템 사용 가이드</h2>
            
            <p><b>1. 감시 시작:</b> [감시 시작] 버튼을 누르면 지정된 폴더를 실시간으로 감시합니다.</p>
            
            <p><b>2. PDF 감지:</b> 측정 완료된 PDF 파일을 감시 폴더에 넣으면 시스템이 자동으로 부품 종류와 측정값을 분석합니다.</p>
            
            <p><b>3. 데이터 입력:</b> 팝업창에서 위치(신관/본관), 차수(초/중/종), 호기 번호를 확인하세요. 
            <br>&nbsp;&nbsp;※ 위치와 호기는 부품별로 기억되며, 차수는 마지막 선택값이 유지됩니다.</p>
            
            <p><b>4. 결과 활용:</b> [엑셀] 버튼으로 데이터를 자동 입력하거나, [카톡] 버튼으로 보고서를 복사해 즉시 전송할 수 있습니다.</p>
            
            <hr>
            
            <p style="background-color: #f8f9fa; padding: 10px; border-left: 5px solid #e74c3c;">
                <b>⚠️ 주의사항 및 안내</b><br>
                본 프로그램은 <b>조원준 사원</b>이 제작하였습니다. <br>
                만약 프로그램 사용 중 오류가 발생할 경우, <b>즉시 사용을 중단하고 기존 수동 매뉴얼 방식으로 업무를 진행</b>해 주세요. <br>
                발생한 오류 내용(로그 창 내용 등)은 조원준 사원에게 공유해 주시면 신속히 조치하겠습니다.
            </p>
            
            <p style="text-align: right; color: #7f8c8d;">v2.0 / Developer: Cho Won-joon</p>
        </div>
        """
        QMessageBox.information(self, "도움말 및 주의사항", help_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())