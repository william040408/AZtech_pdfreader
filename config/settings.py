import json
import os
import sys

# =========================================================
# 1. 경로 기준점 설정 (PyInstaller 배포 대응)
# =========================================================

if getattr(sys, 'frozen', False):
    # .exe 파일로 빌드되어 실행 중인 경우
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # .py 소스 코드로 실행 중인 경우 (AZtech 폴더 기준)
    # 현재 파일 위치(config/settings.py)에서 두 단계 상위로 이동
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================================================
# 2. 고정 디렉토리 경로
# =========================================================

# 감시 및 결과 폴더
WATCH_INPUT_DIR = os.path.join(BASE_DIR, "watch_input")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_output")
FAIL_DIR = os.path.join(BASE_DIR, "fail_output") # 분석 실패 시 이동할 곳 (추천)

# 자산 및 설정 파일 경로
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
REGISTRY_PATH = os.path.join(DATA_DIR, "parts_registry_v2.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "app_settings.json") # 설정값 저장 위치

# =========================================================
# 3. 사용자 설정값(JSON) 관리
# =========================================================

DEFAULT_SETTINGS = {
    "master_save_path": r"C:\CMM_RESULTS",
    "big_cmm_temp": r"C:\TEMP\BIG_CMM",
    "small_cmm_temp": r"C:\TEMP\SMALL_CMM",
    "kakao_report_enabled": True,
    "auto_move_processed": True  # 분석 후 파일 이동 여부
}

def init_directories():
    """필요한 모든 폴더가 없으면 생성합니다."""
    dirs = [WATCH_INPUT_DIR, PROCESSED_DIR, FAIL_DIR, DATA_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_settings():
    """설정 파일을 읽어오거나 없으면 기본값을 반환합니다."""
    init_directories() # 폴더 생성 보장
    
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS) # 없으면 기본값으로 파일 생성
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 설정 로드 실패 (기본값 사용): {e}")
        return DEFAULT_SETTINGS

def save_settings(new_settings):
    """설정값을 JSON 파일로 저장합니다."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ 설정 저장 실패: {e}")

# 앱 구동 시 폴더 구조를 먼저 확보합니다.
init_directories()