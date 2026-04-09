import os
import sys
import time
import json
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication
)
from PyQt5.QtGui import QIcon
from modules.messenger import parse_custom_indices

# [.exe] 빌드 환경과 [.py] 실행 환경 모두를 지원하는 경로 설정
if getattr(sys, 'frozen', False):
    # .exe 실행 시: exe 파일이 있는 폴더
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # .py 실행 시: 현재 소스코드 폴더
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 시스템 경로 추가 (나머지 import들이 정상 작동하게 함)
if BASE_DIR not in sys.path:
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
        self.work_windows = []
        
        # 💡 [수정] 파일에서 설정을 로드하거나 기본값을 사용
        self.app_settings = self.load_settings()

        self.parser = self
        self.is_processing = False
        
        self.watcher_thread = None
        self.btn_toggle_watch.clicked.disconnect()
        self.btn_toggle_watch.clicked.connect(self.toggle_engine)
        self.btn_settings.clicked.connect(self.open_settings)
        
        # 💡 [핵심: 여기에 추가!] 일괄 복사 버튼의 옛날 연결을 끊고 새 함수로 연결합니다.
        try:
            self.btn_batch_process.clicked.disconnect()
        except TypeError:
            pass # 만약 끊을 연결이 없으면 그냥 넘어감
        self.btn_batch_process.clicked.connect(self.open_batch_mode)
        # ------------------------------------------------------------------

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
                "캐리어 250바 작은 삼차원": "", "캐리어 250바 큰 삼차원": "", "캐리어 350바 (일체형 캐리어)": ""
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
            # ✅ 절대 경로로 저장되는지 다시 확인
            save_dir = os.path.dirname(self.CONFIG_FILE)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.app_settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.add_log(f"❌ 설정 저장 실패: {e}")
            return False

    # 💡 [수정됨] 1. 설정 창을 독립된 창으로 띄우기
    def open_settings(self):
        """설정 창 열기 (독립된 별개의 창으로 띄우기)"""
        from ui.settings_dialog import SettingsDialog
        
        # 이미 창이 열려있다면 새로 띄우지 않고 앞으로 가져오기만 함
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # 팝업창 객체를 self에 저장 (창이 바로 꺼지는 현상 방지)
        self.settings_dialog = SettingsDialog(self.app_settings)
        
        # 창이 닫히며(accept) 저장 버튼이 눌렸을 때 _on_settings_saved 실행
        self.settings_dialog.accepted.connect(self._on_settings_saved)
        
        # exec() 대신 show()를 사용해 메인 창과 분리!
        self.settings_dialog.show()

    # 💡 [새로 추가] 설정이 저장될 때 비동기적으로 실행되는 함수
    def _on_settings_saved(self):
        """설정 창이 닫힐 때 실행되는 저장 로직"""
        self.app_settings = self.settings_dialog.get_final_settings()
        if self.save_settings(): 
            self.add_log("⚙️ 설정이 파일에 반영구적으로 저장되었습니다.")
        
        if self.watcher_thread and self.watcher_thread.isRunning():
            self.add_log("⚠️ 감시 폴더 변경을 적용하려면 감시를 중지했다가 다시 시작하세요.")

    # 💡 [새로 추가] 2. 일괄 복사(Batch) 창을 독립된 창으로 띄우기
    def open_batch_mode(self):
        """일괄 엑셀 복사 창 열기 (독립된 별개의 창으로 띄우기)"""
        # 파일명과 클래스명은 사원님의 실제 파일에 맞게 수정하세요 (예: batch_dialog.py)
        from ui.batch_dialog import BatchDialog 
        
        # 이미 열려있으면 앞으로 가져오기
        if hasattr(self, 'batch_dialog') and self.batch_dialog.isVisible():
            self.batch_dialog.raise_()
            self.batch_dialog.activateWindow()
            return

        # self 변수에 담아서 생명 유지
        self.batch_dialog = BatchDialog(main_app=self) 
        
        # 메인 창과 독립적으로 띄우기
        self.batch_dialog.show()

    def execute_save_logic(self, pdf_path, config, measurements, user_data, part_key, dialog):
        """실제 파일을 이동하고 저장하는 로직 (네트워크 vs 파일점유 에러 분리)"""
        try:
            part_display_name = config.get('name', part_key)
            save_paths = self.app_settings.get('save_paths', {})
            custom_save_path = save_paths.get(part_display_name) or save_paths.get(part_key, "")
            
            if not custom_save_path or custom_save_path.strip() == "":
                custom_save_path = PROCESSED_DIR
            
            self.file_mgr.set_base_path(custom_save_path.strip())

            # 🚀 파일 이동 시도
            final_path = self.file_mgr.move_and_save(
                pdf_path, config, measurements, 
                user_data['site'], user_data['machines'], 
                user_data['timing'], user_data['tool_changes'], mode='move'
            ) 

            # [✅ 성공 로직]
            from ui.input_dialog import InputDialog
            InputDialog.save_history()
            self.add_log(f"✅ 분류 저장 완료: {final_path}")
            if dialog:
                dialog.mark_as_saved()

        except PermissionError as e:
            # 📄 1순위: PDF가 열려있는 경우 (파일 접근 거부)
            self.add_log(f"⚠️ 저장 실패: 파일 사용 중 ({e})")
            self._show_custom_alert(
                "📄 파일 사용 중", 
                "해당 PDF가 다른 프로그램에서 열려 있습니다.\n뷰어를 완전히 종료한 후 다시 시도해 주세요.", 
                parent=dialog
            )
            self._restore_save_button(dialog)

        except (OSError, ConnectionError) as e:
            # 🌐 2순위: 랜선/네트워크 드라이브 문제 (경로 없음)
            self.add_log(f"🌐 저장 실패: 경로 접근 불가 ({e})")
            self._show_custom_alert(
                "⚠️ 저장 경로 접근 불가", 
                "서버 연결이 끊겼거나 대상 폴더를 찾을 수 없습니다.\n네트워크 상태를 확인한 후 다시 시도해 주세요.", 
                parent=dialog
            )
            self._restore_save_button(dialog)

        except Exception as e:
            # ❌ 기타 예외
            self.add_log(f"❌ 기타 저장 에러: {e}")
            self._show_custom_alert("❌ 저장 실패", f"예상치 못한 오류가 발생했습니다:\n{str(e)}", parent=dialog)
            self._restore_save_button(dialog)

        finally:
            self.file_mgr.set_base_path(PROCESSED_DIR)

    # ==========================================
    # 🛠️ 에러 처리를 돕는 헬퍼 함수 2개 추가
    # ==========================================
    def _show_custom_alert(self, title, msg, parent=None):
        """커스텀 알림창 띄우기"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent if parent else self, title, msg)

    def _restore_save_button(self, dialog):
        """에러 발생 시 다이얼로그의 버튼을 다시 살려줌"""
        if dialog and hasattr(dialog, 'btn_save'):
            dialog.btn_save.setEnabled(True)
            dialog.btn_save.setText("💾 데이터 분류 저장")
            dialog.btn_save.setStyleSheet("""
                background-color: #e67e22; color: white; 
                font-weight: bold; font-size: 13pt; border-radius: 8px;
            """)
            dialog.btn_save.repaint()

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
        # 1. 파일이 실제로 존재하는지 광속 체크
        if not os.path.exists(pdf_path):
            return
            
        # 💡 [핵심: 초 쿨타임 방어막 생성]
        if not hasattr(self, 'recent_files'):
            self.recent_files = {} # 최근 파일 기록장 생성
            
        current_time = time.time()
        
        # 만약 방금(2초 이내) 감지했던 파일이 또 울리면? -> 무시하고 돌아감!
        if pdf_path in self.recent_files:
            if current_time - self.recent_files[pdf_path] < 10.0:
                return 
                
        # 무사히 통과했다면 현재 시간을 기록장에 작성
        self.recent_files[pdf_path] = current_time

        file_name = os.path.basename(pdf_path)
        self.add_log(f"📂 파일 감지: {file_name}")

        try:
            from io import BytesIO
            import pyperclip
            
            # 파일 읽기
            with open(pdf_path, 'rb') as f:
                pdf_data = BytesIO(f.read())

            # 제품 인식
            res = self.detector.detect_config(pdf_path)
            if not res or not res[0]:
                self.add_log(f"⚠️ [인식 실패] {file_name}")
                self.is_processing = False
                return

            part_key, config = res
            self.add_log(f"✅ 인식 성공: {part_key}")

            # PDF 데이터 추출 및 파싱
            reader = PdfReader(pdf_data)
            full_text = "".join([page.extract_text() + "\n" for page in reader.pages])
            measurements = parse_measurements(full_text, debug=False)
            self.add_log(f"📊 파싱 완료: {len(measurements)}개 항목 감지")

            # 다이얼로그 생성
            from PyQt5.QtCore import Qt
            dialog = InputDialog(file_name, config, None)
            dialog.full_pdf_path = os.path.abspath(pdf_path)
            
            # [수정] 창이 닫힐 때 리스트에서 제거하는 연결
            dialog.finished.connect(lambda: self.work_windows.remove(dialog) if dialog in self.work_windows else None)


            # --- [핵심: handle_action 로직 완성] ---
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
                    # ✨ 카톡 리포트 생성 및 클립보드 복사
                    report, _ = get_part_report(data['site'], m_no, data['timing'], measurements, config, p_idx)
                    pyperclip.copy(report)
                    self.add_log(f"💬 [{m_no}호기] 카톡 보고서 복사 완료!")
                
                elif action_type == "preview":
                    if getattr(self, '_is_previewing', False): return
                    self._is_previewing = True
                    
                    # 💡 1. 실행될 함수 정의 (모든 로직이 이 안에 있어야 함)
                    def run_preview_update():
                        try:
                            machines = data.get('machines', [])
                            print(f"\n[DEBUG] 타이머 실행 - 대상 호기: {machines}")
                            
                            full_debug_text = ""
                            ranges = config.get("data_ranges", [])
                            from PyQt5.QtWidgets import QTextEdit

                            for p_idx, m_no in enumerate(machines):
                                # (1) 리포트 생성
                                try:
                                    report, _ = get_part_report(data['site'], m_no, data['timing'], measurements, config, p_idx)
                                except Exception as e:
                                    report = f"리포트 생성 실패 ({m_no}호기)"
                                    print(f"[ERROR] {m_no}호기 리포트 생성 에러: {e}")

                                # (2) UI 위젯 찾기
                                target_name = f"report_edit_{p_idx}"
                                p_edit = dialog.findChild(QTextEdit, target_name)
                                
                                if p_edit:
                                    p_edit.setPlainText(report)

                                    # 💡 [카톡 필수 부품 하드코딩]
                                    part_name = config.get("name", "")
                                    # 나중에 카톡 필수가 늘어나면 "ACV" in part_name or "다른부품" in part_name 으로 추가하세요!
                                    is_kakao_required = "ACV" in part_name
                                    
                                    # 💡 [색상 분기 로직]
                                    if "ng" in report:
                                        # 🔴 1순위: NG가 1개라도 있는 경우 (빨간색 - 즉시 전송 요망)
                                        p_edit.setStyleSheet("""
                                            background-color: #ffffff; 
                                            color: #c0392b; 
                                            font-weight: bold; 
                                            border: 2px solid #e74c3c; 
                                            border-radius: 5px;
                                            padding: 5px;
                                        """)
                                    elif "un" in report or "up" in report or is_kakao_required:
                                        # 🟠 2순위: NG는 없지만 UN이나 UP이 있는 경우 (주황색 - 카톡 전송 요망)
                                        p_edit.setStyleSheet("""
                                            background-color: #ffffff; 
                                            color: #d35400; 
                                            font-weight: bold; 
                                            border: 2px solid #e67e22; 
                                            border-radius: 5px;
                                            padding: 5px;
                                        """)
                                    else:
                                        # 🟢 3순위: ALL OK 또는 불량이 전혀 없는 상태 (초록색 - 패스 가능)
                                        p_edit.setStyleSheet("""
                                            background-color: #eafaf1; 
                                            color: #27ae60; 
                                            font-weight: bold; 
                                            border: 2px solid #2ecc71; 
                                            border-radius: 5px;
                                            padding: 5px;
                                        """)
                                        
                                    print(f"   ㄴ [SUCCESS] {target_name} 주입 및 3단계 색상 변경 완료")
                                else:
                                    print(f"   ㄴ [FAIL] {target_name} 위젯을 여전히 찾을 수 없음")


                                # (3) 하단 상세 로그 누적
                                full_debug_text += f"=========== [{m_no}호기] 상세 이상 항목 ===========\n"
                                if p_idx < len(ranges):
                                    # 💡 이 부분이 핵심입니다: messenger와 동일한 인덱스 추출 로직 사용
                                    target_pattern = ranges[p_idx]
                                    if not isinstance(target_pattern, list): target_pattern = [target_pattern]
                                    target_indices = parse_custom_indices(target_pattern)

                                    any_issue = False
                                    for abs_idx in target_indices: # 슬라이싱 대신 인덱스 리스트 순회
                                        if abs_idx >= len(measurements): continue
                                        
                                        m = measurements[abs_idx]
                                        status = m.classify().upper() if hasattr(m, 'classify') else "UNKNOWN"
                                        
                                        if status in ["NG", "UN", "UP"]:
                                            any_issue = True
                                            icon = {"NG": "🔴 [NG]", "UN": "🟡 [UN]", "UP": "🟠 [UP]"}.get(status, "⚪")
                                            av = to_f3(getattr(m, 'actual_value', 0.0))
                                            # standard_value가 함수인지 값인지 체크하는 기존 로직 유지
                                            sv_val = getattr(m, 'standard_value', 0.0)
                                            nv = to_f3(sv_val() if callable(sv_val) else sv_val)
                                            
                                            full_debug_text += f"{icon} No.{abs_idx:02d} | {getattr(m, 'name', 'Unknown')}\n"
                                            full_debug_text += f"      ㄴ 측정:{av} (기준:{nv})\n"
                                    
                                    if not any_issue: full_debug_text += "✅ 이상 항목 없음\n"
                                else:
                                    full_debug_text += "⚠️ 범위 설정 없음\n"
                                full_debug_text += "-" * 45 + "\n\n"

                            # (4) 하단 통합 로그창 업데이트
                            dialog.debug_log.setPlainText(full_debug_text)
                            
                        except Exception as preview_e:
                            print(f"[ERROR] 프리뷰 내부 실행 에러: {preview_e}")
                        finally:
                            # 💡 함수 종료 시 플래그 해제 (매우 중요)
                            self._is_previewing = False

                    # 💡 2. 정의한 함수를 0.15초 뒤에 실행하도록 예약
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(150, run_preview_update)

            # [핵심 변경 1] 시그널 연결 (기존과 동일)
            dialog.action_triggered.connect(handle_action)
            dialog.save_requested.connect(lambda d: self.execute_save_logic(pdf_path, config, measurements, d, part_key, dialog))

            # [핵심 변경 2] .exec_()가 아니라 .show()를 사용합니다!
            self.work_windows.append(dialog)
            dialog.show() 
            dialog.raise_()
            dialog.activateWindow()


        except Exception as e:
            self.add_log(f"🔥 에러: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 🌟 [수정] 자식 창과 에러창까지 모두 아우르는 전역 아이콘 설정
    icon_path = os.path.join(BASE_DIR, "assets", "data", "aztech_icon_opaque.ico")
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"⚠️ 아이콘 파일을 찾을 수 없습니다: {icon_path}")

    ex = AZtechApp()
    ex.show()
    sys.exit(app.exec())