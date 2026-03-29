import os
import pyperclip
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt

class BatchDialog(QDialog):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app  # AZtechApp 인스턴스 (detector, parse 기능 활용)
        self.batch_results = {}   # {파일명: (config, measurements)} 저장
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("📂 PDF 일괄 엑셀 복사 모드")
        self.resize(900, 600)
        
        main_layout = QHBoxLayout(self)

        # --- 왼쪽: 파일 리스트 (대기열) ---
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.display_selected_file)
        
        from PyQt5.QtWidgets import QFileDialog
        btn_load = QPushButton("PDF 파일들 불러오기")
        btn_load.setFixedHeight(40)
        btn_load.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_load.clicked.connect(self.load_multiple_pdfs)
        
        left_layout.addWidget(QLabel("📋 작업 대기열"))
        left_layout.addWidget(self.list_widget)
        left_layout.addWidget(btn_load)

        # --- 오른쪽: 상세 정보 및 동적 버튼 구역 ---
        right_layout = QVBoxLayout()
        
        self.lbl_file_title = QLabel("파일을 선택하세요.")
        self.lbl_file_title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2c3e50;")
        self.lbl_file_title.setWordWrap(True)
        
        self.lbl_part_info = QLabel("")
        self.lbl_part_info.setStyleSheet("font-size: 11pt; color: #34495e; margin-bottom: 10px;")

        # 복사 버튼들이 생성될 스크롤 영역
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.button_layout = QVBoxLayout(self.scroll_content)
        self.button_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)

        right_layout.addWidget(self.lbl_file_title)
        right_layout.addWidget(self.lbl_part_info)
        right_layout.addWidget(QLabel("<b>📊 엑셀 클립보드 복사:</b>"))
        right_layout.addWidget(self.scroll)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

    def load_multiple_pdfs(self):
        from PyQt5.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "PDF 선택", "", "PDF Files (*.pdf)")
        if not files: return

        for path in files:
            file_name = os.path.basename(path)
            if file_name in self.batch_results: continue

            try:
                # 1. 어떤 부품인지 감지 (main_app의 detector 사용)
                part_key, config = self.main_app.detector.detect_config(path)
                if not part_key: continue

                # 2. PDF 파싱 (main_app의 parse 함수 사용)
                measurements = self.main_app.parse(path)
                
                # 결과 저장
                self.batch_results[file_name] = (config, measurements)
                self.list_widget.addItem(file_name)
            except Exception as e:
                print(f"파일 분석 실패 ({file_name}): {e}")

    # 1. 버튼 생성 부분 (색상을 처음부터 초록색으로 통일)
    def display_selected_file(self, item):
        file_name = item.text()
        config, measurements = self.batch_results[file_name]

        self.lbl_file_title.setText(f"📄 {file_name}")
        self.lbl_part_info.setText(f"🔎 감지된 부품: {config.get('name', '알 수 없음')}")

        while self.button_layout.count():
            child = self.button_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        mappings = config.get('excel_mapping', [])
        for b_idx, mapping in enumerate(mappings):
            b_name = mapping.get('block_name', f"블록 {b_idx+1}")
            
            btn = QPushButton(f"📊 {b_name}")
            btn.setFixedHeight(50)
            # 처음부터 끝까지 초록색 유지 (보통 상태: 진한 초록 / 마우스 올림: 연한 초록)
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #27ae60; color: white; 
                    font-weight: bold; font-size: 11pt; border-radius: 5px; 
                }
                QPushButton:hover { background-color: #2ecc71; }
            """)
            
            # 버튼 객체(b=btn)를 넘겨주도록 설정
            btn.clicked.connect(lambda chk, c=config, m=measurements, bi=b_idx, b=btn: 
                                self.copy_to_excel(c, m, bi, b))
            self.button_layout.addWidget(btn)

    # 2. 복사 및 빠른 복구 로직 (0.5초 뒤 복구)
    def copy_to_excel(self, config, measurements, block_idx, target_btn):
        from modules.excel_copy import ExcelCopier
        from PyQt5.QtCore import QTimer
        try:
            # 실제 복사 수행
            ExcelCopier(config).copy_part(measurements, p_idx=0, block_idx=block_idx)
            
            # 즉각적인 텍스트 변경
            original_text = target_btn.text()
            target_btn.setText("✅ 복사 완료!")
            
            # 0.5초(500ms) 후에 원래 텍스트로 복구 (거의 바로 돌아옵니다)
            QTimer.singleShot(500, lambda: target_btn.setText(original_text))

        except Exception as e:
            target_btn.setText("❌ 오류")
            QTimer.singleShot(1000, lambda: target_btn.setText("📊 다시 시도"))
            print(f"복사 에러: {e}")