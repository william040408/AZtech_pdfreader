from typing import List, Dict, Tuple

def get_part_report(site: str, machine_no: int, measurements: List, part_config: Dict, part_idx: int) -> Tuple[str, List[str]]:
    """
    보고 멘트와 상세 로그 리스트를 함께 반환합니다.
    """
    ranges = part_config.get("data_ranges", [])
    if part_idx >= len(ranges):
        return "데이터 범위 없음", []

    site_code = "1" if "본관" in site else "2"
    header = f"{site_code}-{machine_no}"

    start, end = ranges[part_idx]
    part_measurements = measurements[start : end + 1]

    ng_avs, un_avs, up_avs = [], [], []
    debug_logs = [] # 상세 확인용 로그

    for i, m in enumerate(part_measurements):
        # 전체 measurements 기준 절대 인덱스 계산
        absolute_idx = start + i
        status = m.classify().upper()
        val = getattr(m, 'actual_value', getattr(m, 'dv', 0))
        val_str = f"{val:.3f}"
        
        # 항목 이름 (m.label 또는 m.name 등이 있다고 가정)
        item_name = getattr(m, 'label', 'Unknown')

        if status == "NG": 
            ng_avs.append(val_str)
            debug_logs.append(f"🔴 [IDX:{absolute_idx}] {item_name}: {val_str} (NG)")
        elif status == "UN": 
            un_avs.append(val_str)
            debug_logs.append(f"🟡 [IDX:{absolute_idx}] {item_name}: {val_str} (UN)")
        elif status == "UP": 
            up_avs.append(val_str)
            debug_logs.append(f"🟠 [IDX:{absolute_idx}] {item_name}: {val_str} (UP)")

    # 멘트 조립
    parts = [header]
    if ng_avs: parts.append(f"ng {' '.join(ng_avs)}")
    if un_avs: parts.append(f"un {' '.join(un_avs)}")
    if up_avs: parts.append(f"up {' '.join(up_avs)}")
    
    if not (ng_avs or un_avs or up_avs):
        parts.append("ALL OK")

    return " ".join(parts), debug_logs