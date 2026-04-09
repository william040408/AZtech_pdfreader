import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
    QButtonGroup, QSpinBox, QPushButton, QCheckBox, QGroupBox, 
    QFrame, QStackedWidget, QWidget, QTextEdit, QMessageBox, QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

class InputDialog(QDialog):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    HISTORY_FILE = os.path.join(BASE_DIR, "assets", "data", "user_history.json")
    
    history = {}
    last_timing = 1

    @classmethod
    def load_history(cls):
        if os.path.exists(cls.HISTORY_FILE) and os.path.getsize(cls.HISTORY_FILE) > 0:
            try:
                with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                    cls.history = json.load(f)
                    cls.last_timing = cls.history.get("_global_last_timing", 1)
            except Exception:
                cls.history = {}

    @classmethod
    def save_history(cls):
        os.makedirs(os.path.dirname(cls.HISTORY_FILE), exist_ok=True)
        try:
            cls.history["_global_last_timing"] = cls.last_timing
            with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(cls.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"히스토리 저장 실패: {e}")

    action_triggered = pyqtSignal(str, dict, object)
    save_requested = pyqtSignal(dict)

    def __init__(self, file_name, config, parent=None):
        super().__init__(parent)
        InputDialog.load_history()
        self.file_name = file_name
        self.config = config
        self.pdf_path = "" # main.py에서 전달받을 수 있도록 준비 (파일 체크용)
        self.part_name = config.get('name', '알 수 없는 부품')
        self.result_data = {} 
        
        # [수정] 한 번만 위로 띄우기 (고정 해제)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        
        self.init_ui()
        self.raise_()
        self.activateWindow()

    def init_ui(self):
        self.setWindowTitle("🛠️ AZtech 작업 콘솔")
        self.setFixedSize(800, 950) 
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # 페이지 1: 호기 설정
        self.setup_page_input()
        # 페이지 2: 결과 확인 및 작업
        self.setup_page_action()
        
        self.stack.setCurrentIndex(0)

    def setup_page_input(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group_style = """
            QGroupBox { font-weight: bold; font-size: 11pt; border: 2px solid #dcdde1; 
                        border-radius: 8px; margin-top: 20px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 15px; padding: 0 5px; color: #2980b9; }
        """

        part_hist = InputDialog.history.get(self.part_name, {"site": "신관", "machines": [0, 0, 0]})

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 2px solid #3498db; padding: 15px;")
        info_layout = QVBoxLayout(info_frame)
        
        part_label = QLabel(self.part_name)
        part_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2c3e50; border: none;")
        part_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(part_label)
        info_layout.addWidget(QLabel(f"📄 파일명: {self.file_name}"))
        layout.addWidget(info_frame)

        row1 = QHBoxLayout()
        site_group = QGroupBox("📍 위치")
        site_group.setStyleSheet(group_style)
        site_box = QHBoxLayout()
        self.radio_new = QRadioButton("신관"); self.radio_main = QRadioButton("본관")
        if part_hist.get("site") == "신관": self.radio_new.setChecked(True)
        else: self.radio_main.setChecked(True)
        site_box.addWidget(self.radio_new); site_box.addWidget(self.radio_main)
        site_group.setLayout(site_box)
        
        timing_group = QGroupBox("⏰ 차수")
        timing_group.setStyleSheet(group_style)
        t_box = QHBoxLayout()
        self.timing_group_btn = QButtonGroup(self)
        for i, text in enumerate(["초물", "중물", "종물"], 1):
            radio = QRadioButton(text); self.timing_group_btn.addButton(radio, i); t_box.addWidget(radio)
            if i == InputDialog.last_timing: radio.setChecked(True)
        timing_group.setLayout(t_box)
        
        row1.addWidget(site_group); row1.addWidget(timing_group)
        layout.addLayout(row1)

        m_group = QGroupBox("🔢 호기 설정")
        m_group.setStyleSheet(group_style)
        m_layout = QVBoxLayout()
        self.machine_spins = []; self.tool_checks = []
        data_count = len(self.config.get('data_ranges', [None]))
        hist_machines = part_hist.get("machines", [0, 0, 0])
        
        for i in range(3):
            row = QHBoxLayout()
            spin = QSpinBox(); spin.setRange(0, 35); spin.setFixedSize(80, 35)
            spin.setValue(hist_machines[i] if i < len(hist_machines) else 0)
            self.machine_spins.append(spin)
            check = QCheckBox("공구교환"); check.setChecked(False); self.tool_checks.append(check)
            row.addWidget(QLabel(f"{i+1}번 호기:")); row.addWidget(spin); row.addSpacing(30); row.addWidget(check); row.addStretch()
            m_layout.addLayout(row)
            if i >= data_count: spin.setEnabled(False); check.setEnabled(False)
            
        m_group.setLayout(m_layout)
        layout.addWidget(m_group)
        layout.addStretch()

        self.btn_next = QPushButton("입력 완료 및 결과 확인 (Enter)")
        self.btn_next.setFixedHeight(60)
        self.btn_next.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; font-size: 15pt; border-radius: 8px;")
        self.btn_next.clicked.connect(self.go_to_action_page)
        layout.addWidget(self.btn_next)
        self.stack.addWidget(page)

    def setup_page_action(self):
        self.action_page = QWidget()
        layout = QVBoxLayout(self.action_page)
        
        # 1. 상단 분석 로그 (고정 높이)
        layout.addWidget(QLabel("<b>🔍 실시간 분석 로그 (모든 호기 합계):</b>"))
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setFixedHeight(250) 
        self.debug_log.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: Consolas; font-size: 10pt; padding: 10px;")
        layout.addWidget(self.debug_log)

        # 2. 중앙 스크롤 영역 (유동적 길이의 핵심)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        # ⭐ 핵심: 위젯들이 위에서부터 차곡차곡 쌓이게 Alignment 설정
        self.scroll_main_layout = QVBoxLayout(scroll_content)
        self.scroll_main_layout.setAlignment(Qt.AlignTop) 
        self.scroll_main_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_main_layout.setSpacing(15) # 카드 사이 간격

        # 💡 여기가 에러의 원인이었던 부분! 이름을 하나로 통일합니다.
        self.content_layout = self.scroll_main_layout 
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 3. 하단 버튼 (저장/종료) - 기존 유지
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("💾 데이터 분류 저장")
        self.btn_save.setFixedHeight(55)
        self.btn_save.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
        self.btn_save.clicked.connect(self.request_save)
        
        self.btn_close = QPushButton("❌ 작업 종료 (창 닫기)")
        self.btn_close.setFixedHeight(55)
        self.btn_close.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
        self.btn_close.clicked.connect(self.accept)
        
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        btn_back = QPushButton("⬅️ 정보 수정으로 돌아가기")
        btn_back.setFixedHeight(35)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(btn_back)

        self.stack.addWidget(self.action_page)

    def request_save(self):
        """저장 버튼 클릭 시 호출"""
        print(f"\n[DIALOG_LOG] --- 저장 요청 시작 ---")
        
        # 1. 파일 점유 체크
        if self.full_pdf_path and os.path.exists(self.full_pdf_path):
            try:
                with open(self.full_pdf_path, 'a') as f:
                    pass 
                print("[DIALOG_LOG] 1. 파일 점유 확인: 통과 (정상)")
            except IOError:
                print("[DIALOG_LOG] 1. 파일 점유 확인: 실패 (사용 중)")
                QMessageBox.critical(self, "파일 접근 오류", f"⚠️ '{self.file_name}' 파일이 열려 있습니다.")
                return

        print(f"[DIALOG_LOG] 3. 버튼 비활성화 및 시그널 전송 준비")
        self.btn_save.setEnabled(False)
        self.btn_save.setText("⏳ 서버 저장 중...")
        self.btn_save.setStyleSheet("background-color: #bdc3c7; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
        QApplication.processEvents() # UI 강제 업데이트

        # 3. 데이터 추출 및 검증
        try:
            data = self.update_and_get_data()
            print(f"[DIALOG_LOG] 2. 데이터 추출 성공: {data}")
            
            # 💡 [수정 포인트] 데이터가 없으면 경고창 띄우고 버튼 다시 살려주기
            if not data['site'] or not data['machines']:
                print("[DIALOG_LOG] 2. 데이터 검증 실패: 필수값 누락")
                QMessageBox.warning(self, "입력 누락", "위치 및 호기 설정을 확인해 주세요.")
                self.btn_save.setEnabled(True)
                self.btn_save.setText("💾 데이터 분류 저장")
                self.btn_save.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
                return 
                
        except Exception as e:
            print(f"[DIALOG_LOG] 2. 데이터 추출 중 에러: {e}")
            self.btn_save.setEnabled(True)
            self.btn_save.setText("💾 데이터 분류 저장")
            return

        # 4. 모든 검증 통과 시 시그널 발생
        self.save_requested.emit(data)
        print(f"[DIALOG_LOG] --- 시그널 발생 완료 ---")

    def update_and_get_data(self):
        current_site = "신관" if self.radio_new.isChecked() else "본관"
        current_machines = [s.value() for s in self.machine_spins]
        InputDialog.last_timing = self.timing_group_btn.checkedId()
        
        InputDialog.history[self.part_name] = {"site": current_site, "machines": current_machines}
        
        timings = {1: "초물", 2: "중물", 3: "종물"}
        self.result_data = {
            "site": current_site,
            "machines": [v for v in current_machines if v > 0],
            "timing_name": timings.get(InputDialog.last_timing, "미정"),
            "timing": InputDialog.last_timing,
            "tool_changes": [c.isChecked() for i, c in enumerate(self.tool_checks) if current_machines[i] > 0]
        }
        return self.result_data

    def go_to_action_page(self):

        # 1. 입력 검증 로직 (기존 유지)
        current_machines = [s.value() for s in self.machine_spins if s.value() > 0]
        if not current_machines:
            QMessageBox.warning(self, "입력 오류", "⚠️ 최소 하나 이상의 호기 번호(1~35)를 입력해야 합니다.")
            return
        if len(current_machines) != len(set(current_machines)):
            QMessageBox.warning(self, "입력 오류", "⚠️ 중복된 호기 번호가 있습니다.")
            return

        # 2. 데이터 업데이트 및 기존 UI 비우기
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): # 레이아웃인 경우 내부 위젯까지 삭제
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget(): sub_item.widget().deleteLater()

        data = self.update_and_get_data()
        self.action_triggered.emit("preview", data, "ALL")

        # 3. 호기별 작업 버튼 생성 로직 (기존 유지)
        mappings = self.config.get('excel_mapping', [])
        num_parts = len(data['machines'])

        for p_idx, m_no in enumerate(data['machines']):
            unit_frame = QFrame()
            unit_frame.setStyleSheet("""
                QFrame { background-color: #fdfdfe; border: 1px solid #dcdde1; border-radius: 10px; margin-bottom: 10px; }
                QLabel { border: none; color: #2c3e50; font-weight: bold; }
            """)
            unit_layout = QVBoxLayout(unit_frame)
            unit_layout.setContentsMargins(15, 10, 15, 15)
            unit_layout.setSpacing(8)

            # 1. 제목 및 요약 멘트 박스
            unit_layout.addWidget(QLabel(f"💬 {m_no}호기 요약:"))
            
            report_edit = QTextEdit()
            report_edit.setReadOnly(True)
            
            # ⭐ 핵심: main.py에서 이 위젯을 찾기 위해 고유 이름을 부여합니다.
            report_edit.setObjectName(f"report_edit_{p_idx}") 
            
            report_edit.setMinimumHeight(60) 
            report_edit.setMaximumHeight(100)
            report_edit.setStyleSheet("background-color: #ffffff; border: 1px solid #ebedef; padding: 5px;")
            unit_layout.addWidget(report_edit)
            
            row = QHBoxLayout()
            
            if num_parts == 1:
                for b_idx, mapping in enumerate(mappings):
                    btn = QPushButton(f"📊 {mapping.get('block_name', f'블록{b_idx+1}')}")
                    btn.setMinimumWidth(160)
                    btn.setFixedHeight(45)
                    btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 5px;")
                    btn.clicked.connect(lambda chk, pi=0, bi=b_idx, b=btn: self.copy_with_feedback(pi, bi, b, data))
                    row.addWidget(btn)
            else:
                if p_idx < len(mappings):
                    btn = QPushButton(f"📊 {mappings[p_idx].get('block_name', f'{p_idx+1}번째')}")
                    btn.setMinimumWidth(200)
                    btn.setFixedHeight(45)
                    btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 5px;")
                    btn.clicked.connect(lambda chk, pi=p_idx, bi=p_idx, b=btn: self.copy_with_feedback(pi, bi, b, data))
                    row.addWidget(btn)

            btn_ka = QPushButton("💬 카톡")
            btn_ka.setFixedSize(90, 45)
            btn_ka.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold; border-radius: 5px;")
            btn_ka.clicked.connect(lambda chk, pi=p_idx, b=btn_ka: self.copy_with_feedback(pi, None, b, data, is_kakao=True))
            row.addWidget(btn_ka)

            unit_layout.addLayout(row)
            
            self.content_layout.addWidget(unit_frame)

        self.stack.setCurrentIndex(1)

    def copy_with_feedback(self, p_idx, b_idx, btn, data, is_kakao=False):
        # 실제 동작 트리거
        if is_kakao:
            self.action_triggered.emit("kakao", data, p_idx)
        else:
            self.action_triggered.emit("excel", data, (p_idx, b_idx))
        
        # 버튼 피드백 설정
        original_text = btn.text()
        original_style = btn.styleSheet()
        
        btn.setText("✅ 완료")
        # 엑셀(초록)이나 카톡(노랑) 배경색은 유지하고 텍스트만 변경
        if is_kakao:
            btn.setStyleSheet("background-color: #f1c40f; color: #2c3e50; font-weight: bold; border-radius: 5px;")
        else:
            btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 5px;")
        
        # 원래대로 복구
        QTimer.singleShot(500, lambda: (
            btn.setText(original_text),
            btn.setStyleSheet(original_style)
        ))

    # 💡 [여기서부터 새로 추가/변경] 안 쓰는 final_accept는 지우고 아래 함수를 넣으세요!
    def mark_as_saved(self):
        """저장이 완료되었을 때 창을 끄지 않고 버튼 상태만 완료로 변경"""
        self.btn_save.setText("✅ 저장 완료")
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
        
        # 이미 이동된 파일을 또 저장하지 못하도록 버튼을 비활성화 (창 닫기 버튼만 누를 수 있게 함)
        self.btn_save.setEnabled(False)