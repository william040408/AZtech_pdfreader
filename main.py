import os
import sys
import time
import pyperclip
import json
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QLabel, QTextEdit, QVBoxLayout, QWidget, QMessageBox
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from core.watcher import AZtechWatcher
from core.detector import PartDetector
from core.parser import parse_measurements
from modules.file_manager import FileManager
from config.settings import WATCH_INPUT_DIR, PROCESSED_DIR, REGISTRY_PATH
from ui.main_window import MainWindow
from ui.input_dialog import InputDialog

from ui.settings_dialog import SettingsDialog # 새로 만든 설정창 import
from PyPDF2 import PdfReader

class WatcherThread(QThread):
    file_detected = pyqtSignal(str)
    log_received = pyqtSignal(str)  # ✨ 새로운 시그널 추가

    def __init__(self, watch_dir):
        super().__init__()
        self.watch_dir = watch_dir
        self.watcher = AZtechWatcher(self.on_detected, watch_dir=self.watch_dir)
        
        # ✨ Watcher의 시그널을 이 쓰레드의 시그널로 연결 (릴레이)
        self.watcher.signals.log_signal.connect(self.log_received.emit)

    def on_detected(self, file_path):
        time.sleep(0.7)
        self.file_detected.emit(file_path)

    def run(self):
        self.watcher.start()
        # QThread의 이벤트 루프를 유지하기 위해 exec() 호출 또는 적절한 대기
        self.exec() 

    def stop(self):
        # 1. 먼저 내부 watcher를 중단시킵니다.
        if hasattr(self, 'watcher'):
            self.watcher.stop()
            
        # 2. QThread의 이벤트 루프를 종료합니다.
        self.quit()
        
        # 3. 쓰레드가 완전히 종료될 때까지 최대 1초 기다립니다.
        if not self.wait(1000): 
            self.terminate() # 1초 뒤에도 안 꺼지면 강제 종료

class AZtechApp(MainWindow):
    def __init__(self):
        super().__init__()
        self.CONFIG_FILE = os.path.join(BASE_DIR, "config", "app_settings.json")
        self.detector = PartDetector(REGISTRY_PATH)
        self.file_mgr = FileManager()
        
        # 💡 [수정] 파일에서 설정을 로드하거나 기본값을 사용
        self.app_settings = self.load_settings()

        self.parser = self
        
        self.watcher_thread = None
        self.btn_toggle_watch.clicked.disconnect()
        self.btn_toggle_watch.clicked.connect(self.toggle_engine)
        self.btn_settings.clicked.connect(self.open_settings)
        
        self.add_log("🚀 AZtech 시스템이 준비되었습니다. (설정 로드 완료)")

    def parse(self, pdf_path):
        """BatchDialog에서 호출할 파싱 브릿지 함수"""
        from PyPDF2 import PdfReader
        from core.parser import parse_measurements
        
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # 기존에 쓰시던 파싱 함수를 호출하여 결과를 반환합니다.
        return parse_measurements(full_text, debug=False)    

    def load_settings(self):
        """JSON 파일에서 설정 불러오기"""
        default_settings = {
            'watch_dir': WATCH_INPUT_DIR,
            'save_paths': {
                "센서바디 450바 1개": "", "센서바디 450바 2개": "", "센서바디 450바 3개": "",
                "센서바디 350바 1개": "", "센서바디 350바 2개": "", "센서바디 350바 3개": "",
                "다이아 프램 정면": "", "다이아 프램 배면": "", 
                "센서하우징 17.92": "", "센서하우징 19.25": "", "절곡형": "",
                "캐리어 250바 작은 삼차원": "", "캐리어 250바 큰 삼차원": ""
            }
        }
        
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 기본 구조 유지하면서 덮어쓰기 (새로운 프로그램 추가 대비)
                    default_settings.update(loaded)
                    return default_settings
            except Exception as e:
                print(f"설정 로드 에러: {e}")
        return default_settings

    def save_settings(self):
        """현재 설정을 JSON 파일로 저장"""
        try:
            # config 폴더가 없으면 생성
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.app_settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.add_log(f"❌ 설정 저장 실패: {e}")
            return False

    def open_settings(self):
        """설정 창 열기 및 변경 시 파일 저장"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.app_settings)
        if dialog.exec():
            self.app_settings = dialog.get_final_settings()
            if self.save_settings(): # 💡 변경 즉시 파일에 저장!
                self.add_log("⚙️ 설정이 파일에 반영구적으로 저장되었습니다.")
            
            if self.watcher_thread and self.watcher_thread.isRunning():
                self.add_log("⚠️ 감시 폴더 변경을 적용하려면 재시작하세요.")

    def toggle_engine(self):
        if self.watcher_thread and self.watcher_thread.isRunning():
            self.watcher_thread.stop()
            
            # UI 변경: 다시 시작할 수 있도록 초록색으로
            self.btn_toggle_watch.setText("감시 시작")
            self.btn_toggle_watch.setStyleSheet("""
                background-color: #2ecc71; color: white; 
                border-radius: 10px; border: none; font-weight: bold;
            """)
            self.lbl_status.setText("대기 중")
            self.lbl_status.setStyleSheet("color: #7f8c8d; border: none;")
            
            # 로그는 이제 watcher.signals에서 자동으로 날아오지만, 
            # 버튼 클릭 직관성을 위해 직접 남겨줍니다.
            self.statusBar().showMessage("준비 완료")
        else:
            watch_target = self.app_settings.get('watch_dir', WATCH_INPUT_DIR)
            self.watcher_thread = WatcherThread(watch_target)
            
            # 시그널 연결
            self.watcher_thread.file_detected.connect(self.process_new_file)
            self.watcher_thread.log_received.connect(self.add_log) 
            
            self.watcher_thread.start()
            
            # UI 변경: 중지할 수 있도록 빨간색으로
            self.btn_toggle_watch.setText("감시 중지")
            self.btn_toggle_watch.setStyleSheet("""
                background-color: #e74c3c; color: white; 
                border-radius: 10px; border: none; font-weight: bold;
            """)
            self.lbl_status.setText("🔍 실시간 감시 중...")
            self.lbl_status.setStyleSheet("color: #e74c3c; border: none;")
            
            self.statusBar().showMessage("감시 엔진 작동 중...")

    def process_new_file(self, pdf_path):
        file_name = os.path.basename(pdf_path)
        self.add_log(f"📂 파일 감지: {file_name}")

        try:
            part_key, config = self.detector.detect_config(pdf_path)
            if not part_key: return

            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
                
            measurements = parse_measurements(full_text, debug=False)
            dialog = InputDialog(file_name, config, self)
            
            def handle_action(action_type, data, info=None):
                from modules.excel_copy import ExcelCopier
                from modules.messenger import get_part_report
                
                def to_f3(val):
                    try: return f"{float(val):.3f}"
                    except: return str(val)

                if action_type == "excel":
                    p_idx, b_idx = info
                    m_no = data['machines'][p_idx]
                    ExcelCopier(config).copy_part(measurements, p_idx, block_idx=b_idx)
                    b_name = config['excel_mapping'][b_idx]['block_name']
                    self.add_log(f"📊 [{m_no}호기] '{b_name}' 복사 완료!")
                
                elif action_type == "kakao":
                    p_idx = info
                    m_no = data['machines'][p_idx]
                    report, _ = get_part_report(data['site'], m_no, measurements, config, p_idx)
                    pyperclip.copy(report)
                    self.add_log(f"💬 [{m_no}호기] 카톡 보고서 복사 완료!")
                
                elif action_type == "preview":
                    while dialog.preview_container.count():
                        item = dialog.preview_container.takeAt(0)
                        if item.widget(): item.widget().deleteLater()
                        elif item.layout():
                            while item.layout().count():
                                child = item.layout().takeAt(0)
                                if child.widget(): child.widget().deleteLater()

                    all_parts_ms = measurements if isinstance(measurements[0], list) else [measurements]
                    
                    for p_idx in range(len(data['machines'])):
                        m_no = data['machines'][p_idx]
                        report, _ = get_part_report(data['site'], m_no, measurements, config, p_idx)
                        lbl = QLabel(f"<b>💬 {m_no}호기:</b>")
                        p_edit = QTextEdit()
                        p_edit.setReadOnly(True)
                        p_edit.setPlainText(report)
                        p_edit.setFixedHeight(65) # 시원하게 65로 소폭 조정
                        p_edit.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdde1; font-size: 9pt;")
                        dialog.preview_container.addWidget(lbl)
                        dialog.preview_container.addWidget(p_edit)

                    curr_p_idx = info if (info is not None and isinstance(info, int)) else 0
                    if curr_p_idx >= len(all_parts_ms): curr_p_idx = 0
                    m_no = data['machines'][curr_p_idx] if data['machines'] else "?"
                    target_ms = all_parts_ms[curr_p_idx]
                    debug_text = f"--- [{m_no}호기] 이상 항목(NG/UP/UN) 리스트 ---\n"
                    bad_items_found = False
                    for i, m in enumerate(target_ms):
                        status = m.classify().upper()
                        if status in ["NG", "UP", "UN"]:
                            bad_items_found = True
                            
                            # 💡 [수정] 속성이 있는지 확인하며 안전하게 값 추출
                            av = to_f3(getattr(m, 'actual_value', 0.0))
                            ut = to_f3(getattr(m, 'ut', 0.0))
                            lt = to_f3(getattr(m, 'lt', 0.0))
                            
                            # nv가 없으면 dv를 시도하고, 둘 다 없으면 "0.000"
                            nv_val = getattr(m, 'nv', getattr(m, 'dv', 0.0))
                            nv = to_f3(nv_val)
                            
                            display_name = f"[{m.cat}] {m.name}"
                            if len(display_name) > 25: display_name = display_name[:22] + "..."
                            debug_text += f"❌ {i:02d} | {status} | {display_name}\n"
                            if hasattr(m, 'nv'): debug_text += f"   ㄴ 값:{av} (기준:{nv} / {lt}~{ut})\n"
                            else: debug_text += f"   ㄴ 값:{av} (공차:{to_f3(m.to)})\n"
                            debug_text += "-" * 35 + "\n"
                    if not bad_items_found: debug_text += "✅ 모든 측정 항목이 정상(OK)입니다!\n"
                    dialog.debug_log.setPlainText(debug_text)

            dialog.action_triggered.connect(handle_action)

            if dialog.exec():
                user_data = dialog.result_data
                
                # 💡 [핵심] 프로그램 종류에 맞는 개별 저장 경로 가져오기
                custom_save_path = self.app_settings['save_paths'].get(part_key, PROCESSED_DIR)
                self.file_mgr.set_base_path(custom_save_path) # 임시로 저장 경로 변경
                
                final_path = self.file_mgr.move_and_save(
                    pdf_path, config, measurements,
                    user_data['site'], user_data['machines'], user_data['timing'],
                    user_data['tool_changes'], mode='move'
                )
                if final_path: self.add_log(f"✅ 작업 완료: {final_path}")
                
                # 다음 파일을 위해 기본 경로로 복구 (필요시)
                self.file_mgr.set_base_path(PROCESSED_DIR)

        except Exception as e:
            self.add_log(f"🔥 에러: {str(e)}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AZtechApp()
    ex.show()
    sys.exit(app.exec())