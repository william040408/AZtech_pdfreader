# 🛠️ AZtech PDF 데이터 자동화 시스템 v2.0

현장의 측정 PDF 데이터를 실시간으로 분석하여 엑셀 입력 및 카카오톡 보고를 자동화하는 생산 효율화 프로그램입니다.
본 프로그램은 **Windows 7 환경**에서도 최적의 퍼포먼스를 내도록 설계되었습니다.

---

## ✨ 주요 기능

### 🔍 실시간 폴더 감시

설정된 폴더에 새 PDF 파일이 생성되면 즉시 감지하여 작업 콘솔을 실행합니다.

### 🧬 지능형 데이터 추출

PDF 내 수백 개의 측정 항목 중 `data_ranges`에 정의된 핵심 치수만 정규표현식(Regex)으로 정확히 골라냅니다.

### ⚠️ 실시간 분석 로그

추출된 데이터 중 **NG, UP, UN(공차 인접)** 항목을 실시간 로그창에 즉시 표시하여 육안 검사를 보조합니다.

### 🧠 스마트 히스토리

부품별로 직전 작업 위치(신관/본관)와 호기 번호를 기억하여 반복 입력 시간을 단축합니다.

### ⚡ 멀티 액션 피드백

* 📊 **Excel 자동 입력**
  클릭 한 번으로 지정된 엑셀 시트의 셀에 데이터를 기입합니다. (완료 시 버튼 피드백 제공)

* 💬 **카톡 보고서**
  보고 양식에 맞춘 텍스트를 클립보드에 자동 복사합니다. (완료 시 버튼 피드백 제공)

### 💡 [NEW] 수동/일괄 Excel 처리

실시간 감시를 놓쳤거나 과거의 PDF 파일들을 처리해야 할 때 사용합니다.

* `[📂 일괄 엑셀 처리하기]` 버튼을 통해 PDF 파일을 수동으로 선택
* 데이터를 즉시 추출하여 엑셀 시트를 자동으로 띄움

---

## 📂 프로젝트 구조

```text
AZtech
├─ core/                # 분석 엔진 (Watcher, Detector, Parser, Data Model)
├─ ui/                  # PyQt5 기반 인터페이스 (Main, Input, Settings, Batch)
│  └─ batch_dialog.py   # [NEW] 수동/일괄 처리를 위한 다이얼로그
├─ modules/             # 외부 연동 모듈 (Excel, Messenger, FileManager)
├─ assets/              # 리소스 (아이콘, 부품 시그니처 레지스트리)
├─ config/              # 전역 설정 및 개별 부품별 추출 범위(JSON)
├─ watch_input/         # [감시 대상 폴더] - 설정에서 변경 가능
└─ main.py              # 프로그램 실행 엔트리 포인트
```

---

## 💻 실행 및 빌드 환경

* **OS**: Windows 7 / 10 / 11 (64-bit)
* **Language**: Python 3.8.10 (Win7 호환 마지막 공식 버전)
* **Core Library**: PyQt5, PyInstaller, Watchdog, PyPDF2, pyperclip

---

## 🛠️ 개발자용 빌드 가이드 (Windows 7 호환)

가장 안정적인 빌드를 위해 아래 명령어를 권장합니다. (데이터 파일 포함 필수)

```bash
# 1. 환경 구축 및 라이브러리 설치
# (venv38 등의 가상환경 사용을 권장합니다)
pip install -r requirements.txt

# 2. EXE 빌드 (설정 및 리소스 폴더 포함)
pyinstaller --noconfirm --onedir --windowed \
--add-data "assets;assets" \
--add-data "config;config" \
--add-data "ui;ui" \
--add-data "core;core" \
--add-data "modules;modules" \
--icon="assets/data/aztech_icon.ico" \
--name "AZtech_v2.0_Console" main.py
```

---

## ⚠️ 주의사항 및 안내

* **제작자**: 조원준 사원 (william0408)

* **오류 관리**
  프로그램 실행 중 예기치 못한 에러 발생 시, 우측 하단의 로그창 내용을 캡처하여 개발자에게 전달 부탁드립니다.

* **백업**
  자동화 도구는 보조 수단입니다. 중요 데이터는 반드시 엑셀 저장 후 최종 확인 과정을 거쳐주세요.
