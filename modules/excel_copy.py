import pyperclip
from typing import List, Dict, Any

class ExcelCopier:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # excel_mapping 구조: [{"block_name": "...", "mappings": [...]}, ...]
        self.mapping_groups = config.get("excel_mapping", [])

    def _extract_value(self, item: Dict, measurements: List) -> str:
        """값 추출 로직"""
        source_type = item.get("source_type", "pdf_idx")
        v_source = item.get("value_source")

        try:
            if source_type == "pdf_idx":
                m = measurements[int(v_source)]
                val = getattr(m, 'actual_value', getattr(m, 'dv', 0))
                return f"{val:.3f}"
            
            elif source_type == "fixed":
                return str(v_source)
            
            elif source_type in ["max", "min"]:
                indices = v_source if isinstance(v_source, list) else [v_source]
                values = []
                for i in indices:
                    m = measurements[int(i)]
                    values.append(getattr(m, 'actual_value', getattr(m, 'dv', 0)))
                
                result = max(values) if source_type == "max" else min(values)
                return f"{result:.3f}"
            
            return ""
        except (IndexError, ValueError, TypeError, AttributeError):
            return "ERR"

    # 💡 [중요 수정] 인자를 3개 받도록 변경 (measurements, p_idx, block_idx)
    def copy_part(self, measurements: List, p_idx: int, block_idx: int = 0):
        """
        measurements: 전체 측정 데이터 (리스트의 리스트 구조인 경우 대비)
        p_idx: 몇 번째 호기(부품)인지
        block_idx: 해당 부품 내에서 몇 번째 엑셀 블록인지
        """
        if not self.mapping_groups or block_idx >= len(self.mapping_groups):
            print(f"❌ 해당 블록({block_idx + 1}번)의 설정 정보가 없습니다.")
            return

        # 💡 [핵심] 만약 measurements가 [부품1데이터, 부품2데이터...] 구조라면 
        # 선택한 호기에 맞는 데이터를 먼저 타겟팅합니다.
        # (일반적으로 리스트의 리스트 형태이므로 p_idx로 접근)
        try:
            target_measurements = measurements[p_idx] if isinstance(measurements[0], list) else measurements
        except (IndexError, TypeError):
            target_measurements = measurements

        target_block = self.mapping_groups[block_idx]
        block_name = target_block.get("block_name", f"구역 {block_idx + 1}")
        current_mappings = target_block.get("mappings", [])

        if not current_mappings:
            print(f"⚠️ '{block_name}'에 복사할 매핑 데이터가 없습니다.")
            return

        # 1. 최대 행 번호 확인
        try:
            max_row = max(item['row_idx'] for item in current_mappings)
        except ValueError:
            return
        
        # 2. 결과 리스트 생성
        output_rows = [""] * (max_row + 1)

        # 3. 데이터 채우기 (타겟팅된 측정값 사용)
        for item in current_mappings:
            r_idx = item['row_idx']
            if r_idx < len(output_rows):
                val = self._extract_value(item, target_measurements)
                output_rows[r_idx] = val

        # 4. 클립보드 복사
        final_string = "\n".join(output_rows[1:])
        pyperclip.copy(final_string)
        
        print(f"✅ [Excel] '{block_name}' 데이터가 클립보드에 복사되었습니다.")