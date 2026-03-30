import json
import os
import sys

# =========================================================
# 1. 경로 기준점 설정 (PyInstaller 배포 대응)
# =========================================================

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # config/ 폴더 안에 있으므로 두 번 올라가서 AZtech 루트 폴더를 잡음
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================================================
# 2. 고정 디렉토리 경로
# =========================================================

# 2. 디렉토리 경로 설정
WATCH_INPUT_DIR = os.path.join(BASE_DIR, "watch_input")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_output")
FAIL_DIR = os.path.join(BASE_DIR, "fail_output")

# 자산 폴더 (읽기 전용 레시피북)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
REGISTRY_PATH = os.path.join(DATA_DIR, "parts_registry_v2.json")

# 설정 폴더 (사용자 개별 설정 저장소 - 여기가 훨씬 안전합니다!)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "app_settings.json")

# =========================================================
# 3. 사용자 설정값(JSON) 관리
# =========================================================

# 3. 사용자 설정값 기본값 (권한 문제가 없는 폴더 기준)
DEFAULT_SETTINGS = {
    "watch_dir": WATCH_INPUT_DIR,
    "master_save_path": PROCESSED_DIR, # 기본은 내 폴더 안으로!
    "kakao_report_enabled": True,
    "auto_move_processed": True
}

def init_directories():
    """필요한 모든 폴더가 없으면 생성합니다."""
    # CONFIG_DIR도 목록에 추가해야 합니다!
    dirs = [WATCH_INPUT_DIR, PROCESSED_DIR, FAIL_DIR, DATA_DIR, CONFIG_DIR]
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