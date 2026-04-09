import os
import json
from PyPDF2 import PdfReader  # utils 대신 PyPDF2 직접 사용

import sys
# 현재 파일의 부모 폴더(AZtech)를 경로에 추가
current_file_path = os.path.abspath(__file__)
# 두 단계 위로 올라가서 'AZtech' 폴더 경로를 잡습니다.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))

if project_root not in sys.path:
    sys.path.append(project_root)

# 이제 core를 가져올 수 있습니다.
from core.parser import parse_measurements

# --- 설정 ---
TARGET_PDF = r"samples\sample_pdf2\종품.pdf"  # 경로 오타(ssample -> sample) 주의하세요!
OUTPUT_DIR = "helper_outputs"

def generate_helper_data():
    if not os.path.exists(TARGET_PDF):
        print(f"❌ 파일을 찾을 수 없습니다: {TARGET_PDF}")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    base_name = os.path.splitext(os.path.basename(TARGET_PDF))[0]
    output_filename = os.path.join(OUTPUT_DIR, f"signature_helper_{base_name}.txt")

    print(f"🔍 [전체 항목] 순서 분석 시작: {TARGET_PDF}...")

    # --- [수정] PyPDF2로 직접 텍스트 추출 ---
    try:
        reader = PdfReader(TARGET_PDF)
        raw_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"
    except Exception as e:
        print(f"❌ PDF 읽기 오류: {e}")
        return

    # 파서 호출
    measurements = parse_measurements(raw_text)
    
    if not measurements:
        print("❌ 파싱된 데이터가 없습니다. 파서(parser.py) 설정을 확인하세요.")
        return

    # 모든 항목 이름을 리스트에 담음
    full_ordered_signature = [m.name for m in measurements]

    # 결과 리포트 작성
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"==================================================\n")
            f.write(f"  [FULL STRICT MATCHING REPORT]\n")
            f.write(f"  PDF: {os.path.basename(TARGET_PDF)}\n")
            f.write(f"  * 이 리스트는 0번부터 {len(full_ordered_signature)-1}번까지 모든 순서를 포함합니다.\n")
            f.write(f"==================================================\n\n")
            
            # --- 파트 1: JSON 복붙용 Signature ---
            f.write("[PART 1: JSON Signature List - ALL ITEMS IN ORDER]\n")
            f.write("이 내용을 그대로 복사해서 JSON의 \"signature\": [...] 안에 넣으세요.\n")
            f.write("-" * 50 + "\n")
            
            # JSON 포맷으로 예쁘게 변환 (인덴트 4칸)
            json_sig = json.dumps(full_ordered_signature, indent=4, ensure_ascii=False)
            
            # 리스트 통째로 출력 (앞뒤 대괄호 포함하는 게 JSON 구조상 더 편할 거예요)
            f.write(json_sig) 
            f.write("\n" + "-" * 50 + "\n\n\n")
            
            # --- 파트 2: 확인용 인덱스 매핑 ---
            f.write("[PART 2: Index Mapping for Verification]\n")
            f.write("-" * 50 + "\n")
            for i, name in enumerate(full_ordered_signature):
                f.write(f"[{i:3}] {name}\n")
            f.write("-" * 50 + "\n")

        print(f"✅ 분석 완료! 총 {len(full_ordered_signature)}개 항목이 등록되었습니다.")
        print(f"📂 파일 확인: {output_filename}")
        
    except Exception as e:
        print(f"❌ 파일 쓰기 오류: {e}")

if __name__ == "__main__":
    generate_helper_data()