import os
import json
import difflib
from PyPDF2 import PdfReader
# 제작하신 parser.py에서 측정 항목 추출 함수를 가져옵니다.
from core.parser import parse_measurements

class PartDetector:
    def __init__(self, json_path: str):
        """
        json_path: 부품 정보가 담긴 parts_registry_v2.json 경로
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        except FileNotFoundError:
            print(f"❌ [ERROR] 설정 파일을 찾을 수 없습니다: {json_path}")
            self.registry = {}
        except Exception as e:
            print(f"❌ [ERROR] JSON 로드 중 오류 발생: {e}")
            self.registry = {}

    def detect_config(self, pdf_path: str):
        """
        PDF를 파싱하여 signature가 100% 일치하는 부품의 [키, 설정값]을 반환.
        일치하지 않으면 가장 유사한 부품과 비교 리포트를 출력함.
        """
        try:
            # 1. PDF 텍스트 추출
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # 2. 파서를 통해 실제 측정 항목 이름들(Signature) 추출
            measurements = parse_measurements(full_text)
            extracted_names = [m.name for m in measurements]

            if not extracted_names:
                print(f"⚠️ [WARN] PDF에서 측정 항목을 찾지 못했습니다: {pdf_path}")
                return None, None

            clean_extracted = [name.replace(" ", "") for name in extracted_names]

            best_match_key = None
            max_ratio = 0.0

            for part_key, config in self.registry.items():
                json_sig = config.get("signature", [])
                
                # JSON에 등록된 signature도 공백을 제거해서 준비
                clean_json_sig = [name.replace(" ", "") for name in json_sig]
                
                # 3. 공백 제거 후 100% 일치 비교 (Lenient Match)
                if clean_extracted == clean_json_sig:
                    # 매칭 성공 시 실제 원본 데이터와 설정값 반환
                    return part_key, config
                
                # 일치하지 않을 경우, 디버깅을 위한 유사도 계산 (공백 제거 버전 기준)
                ratio = difflib.SequenceMatcher(None, clean_extracted, clean_json_sig).ratio()
                if ratio > max_ratio:
                    max_ratio = ratio
                    best_match_key = part_key

            # 4. 100% 일치 실패 시 상세 오류 리포트 출력
            self._print_error_report(pdf_path, extracted_names, best_match_key, max_ratio)
            return None, None

        except Exception as e:
            print(f"❌ [ERROR] Detector 실행 중 오류 발생: {e}")
            return None, None

    def _print_error_report(self, pdf_path, extracted_names, best_key, ratio):
        """가장 유사한 부품과 1:1 대조하여 차이점을 출력 (디버깅용)"""
        print("\n" + "!" * 60)
        print(f"🚨 [부품 인식 실패] 일치하는 Signature를 찾을 수 없습니다!")
        print(f"📄 대상 파일: {os.path.basename(pdf_path)}")
        
        if best_key:
            target_sig = self.registry[best_key].get("signature", [])
            print(f"🔍 가장 의심되는 후보: '{best_key}' (유사도 {ratio*100:.1f}%)")
            print("-" * 60)
            print("👇 [차이점 분석] -: PDF에서 추출됨 / +: JSON에 등록됨")
            
            # ndiff를 사용하여 줄 단위 차이점 계산
            diff = list(difflib.ndiff(extracted_names, target_sig))
            
            diff_found = False
            for line in diff:
                # 변경된 부분(- 또는 +)만 골라서 출력
                if line.startswith('- ') or line.startswith('+ '):
                    print(f"   {line.strip()}")
                    diff_found = True
            
            if not diff_found:
                print("   (항목 내용은 같으나 순서가 다르거나 리스트 구조가 다릅니다.)")
        else:
            print("❓ 등록된 부품 중 유사한 항목이 전혀 없습니다. JSON 등록 상태를 확인하세요.")
            
        print("-" * 60)
        print(f"💡 위 차이점(-, +)을 확인하여 JSON의 'signature'를 수정하세요.")
        print("!" * 60 + "\n")

# 테스트 코드 (직접 실행 시)
if __name__ == "__main__":
    detector = PartDetector("data/parts_registry_v2.json")
    # 예시 실행 코드
    # key, conf = detector.detect_config("sample_pdf2/절곡형.pdf")