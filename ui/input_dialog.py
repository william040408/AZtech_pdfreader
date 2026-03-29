import sys
import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
    QButtonGroup, QSpinBox, QPushButton, QCheckBox, QGroupBox, 
    QFrame, QStackedWidget, QWidget, QTextEdit, QMessageBox, QScrollArea
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

    def __init__(self, file_name, config, parent=None):
        super().__init__(parent)
        InputDialog.load_history()
        
        self.file_name = file_name
        self.config = config
        self.part_name = config.get('name', '알 수 없는 부품')
        
        # [해결] main.py에서 참조하는 변수 선언
        self.result_data = {} 
        
        # [설정] 창을 항상 위로 & 자동 포커스
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.init_ui()
        self.raise_()
        self.activateWindow()

    def init_ui(self):
        self.setWindowTitle("🛠️ AZtech 작업 콘솔")
        # 요청하신 대로 세로 길이를 950으로 더 확장했습니다.
        self.setFixedSize(800, 950) 
        
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        self.setup_page_input()
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
        
        # [확장] 디버깅 로그 길이 확장 (350으로 더 키웠습니다)
        layout.addWidget(QLabel("<b>🔍 실시간 분석 로그 (NG 판정 근거):</b>"))
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setFixedHeight(350) 
        self.debug_log.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: Consolas; font-size: 10pt; padding: 10px;")
        layout.addWidget(self.debug_log)

        # [스크롤] 내용이 길어져도 버튼이 안 잘리게 스크롤 영역 사용
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        
        self.preview_container = QVBoxLayout()
        self.scroll_layout.addLayout(self.preview_container)

        self.dyn_layout = QVBoxLayout()
        self.scroll_layout.addLayout(self.dyn_layout)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.btn_done = QPushButton("💾 작업 데이터 저장 및 종료")
        self.btn_done.setFixedHeight(55)
        self.btn_done.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; font-size: 13pt; border-radius: 8px;")
        self.btn_done.clicked.connect(self.final_accept)
        layout.addWidget(self.btn_done)

        btn_back = QPushButton("⬅️ 정보 수정으로 돌아가기")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(btn_back)

        self.stack.addWidget(self.action_page)

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
        data = self.update_and_get_data()
        
        while self.dyn_layout.count():
            item = self.dyn_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        mappings = self.config.get('excel_mapping', [])
        num_parts = len(data['machines'])

        for p_idx, m_no in enumerate(data['machines']):
            label = QLabel(f"<b>[ {m_no}호기 작업 ]</b>")
            label.setStyleSheet("margin-top: 10px; color: #34495e;")
            self.dyn_layout.addWidget(label)
            
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
            
            self.dyn_layout.addLayout(row)

        self.action_triggered.emit("preview", data, 0)
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

    def final_accept(self):
        InputDialog.save_history()
        self.accept()