from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLineEdit, QPushButton, QLabel, QFileDialog, QWidget
)

class SettingsDialog(QDialog):
    def __init__(self, current_settings):
        super().__init__()
        self.setWindowTitle("시스템 설정")
        self.setMinimumSize(600, 500)
        self.settings = current_settings # dict 형태 (감시경로, 프로그램별 저장경로)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # [1] 감시 폴더 설정
        layout.addWidget(QLabel("<b>🔍 PDF 감시 폴더 설정</b>"))
        watch_layout = QHBoxLayout()
        self.watch_path_edit = QLineEdit(self.settings.get('watch_dir', ''))
        btn_browse_watch = QPushButton("폴더 선택")
        btn_browse_watch.clicked.connect(lambda: self._browse('watch'))
        watch_layout.addWidget(self.watch_path_edit)
        watch_layout.addWidget(btn_browse_watch)
        layout.addLayout(watch_layout)
        
        layout.addWidget(QLabel("<br><b>📁 프로그램별 저장 경로 설정</b>"))
        
        # [2] 프로그램별 경로 (스크롤 영역)
        scroll = QScrollArea()
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        
        self.path_edits = {}
        programs = [
            "센서바디 450바 1개", "센서바디 450바 2개", "센서바디 450바 3개",
            "센서바디 350바 1개", "센서바디 350바 2개", "센서바디 350바 3개",
            "다이아 프램 정면", "다이아 프램 배면", 
            "센서하우징 17.92", "센서하우징 19.25", "절곡형",
            "캐리어 250바 작은 삼차원", "캐리어 250바 큰 삼차원", "캐리어 350바 (일체형 캐리어)", "센서포트", "ACV"
        ]
        
        for prog in programs:
            p_layout = QHBoxLayout()
            p_label = QLabel(f"<b>{prog}</b>")
            p_label.setFixedWidth(220)
            
            # 경로가 없으면 '경로 미지정' 표시
            current_path = self.settings.get('save_paths', {}).get(prog, '')
            p_edit = QLineEdit(current_path)
            p_edit.setPlaceholderText("기본 폴더 사용 (미지정)") 
            
            btn_p_browse = QPushButton("폴더 선택")
            btn_p_browse.clicked.connect(lambda checked, p=prog: self._browse(p))
            
            p_layout.addWidget(p_label)
            p_layout.addWidget(p_edit)
            p_layout.addWidget(btn_p_browse)
            self.path_edits[prog] = p_edit
            self.scroll_layout.addLayout(p_layout)
            
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # 저장 버튼
        btn_save = QPushButton("설정 저장 및 닫기")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def _browse(self, key):
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            if key == 'watch': self.watch_path_edit.setText(path)
            else: self.path_edits[key].setText(path)

    def get_final_settings(self):
        return {
            'watch_dir': self.watch_path_edit.text(),
            'save_paths': {k: v.text() for k, v in self.path_edits.items()}
        }