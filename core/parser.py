import re
from core.models import NominalMeasurement, ToleranceMeasurement

def parse_measurements(text: str, excluded_keywords=None, debug=False):
    results = []
    excluded_keywords = [] if excluded_keywords is None else excluded_keywords
    
    NOMINAL_CATS = ["위치", "직경", "거리"]
    TOLERANCE_CATS = ["동심도", "원주 흔들림", "축 흔들림", "진원도", "직각도", "평행도", "위치도", "평면도"]
    REQUIRED_KEYS = ["NV", "UT", "LT", "TO", "DV", "AV", "YN", "ZN", "ZA", "XN", "XA", "YA"]
    
    # 일반적인 단어 제외 리스트
    ELIMINATE_KEYS = [
        "벤딩피팅", "공정검사", "완료", "치수검사", "센서바디1", "센서바디2", "센서바디3", 
        "샘플트레이", "캐리어", "일체형", "체크포인트", "추가포인트", "태영", "센서바디", "센서 하우징",
        "Carrier"
    ]
    
    # --- [STEP 0] 전처리 (Cleaning) ---
    if debug: print("\n[DEBUG] --- STEP 0: 전처리 시작 ---")

    # 2. ER= 노이즈 제거 (이건 유지)
    text = re.sub(r'ER=[ \-|<>]*\s*(-?\d+\.\d+)', ' ', text)

    text = re.sub(r'[\-|<>]{2,}', ' ', text)

    # 3. 불필요한 바(|) 기호 제거
    text = text.replace('|', ' ')

    # 1. 프로그램 이름 및 경로 패턴 삭제 (숫자 간섭 방지용 핵심 로직)
    # 6.1이나 AZ-TECH 뒤의 숫자가 데이터로 오인되지 않게 패턴으로 지웁니다.
    ELIMINATE_PATTERNS = [
        r"GEOPAK\s+v\d+\.\d+\.R\d+",              # GEOPAK v3.4.R1 등
        r"AZ-TECH\s+\d+",                         # AZ-TECH 1, 2, 3 등
        r"\d+\.[\w\s\.]+\d+\.\d+.*?,.*?\d+",      # 1.carrier 6.1... , 1 같은 복잡한 경로
        r"\[mm\]",                                # 단위 표시
        r"\d+\.\s*CA\s*\d+BAR.*?,?\s*\d+",        # 1. CA 250BAR-2, 1 등
        r"\d+\.\s*B\.F\s*일자형.*?,?\s*\d+",       # 1. B.F 일자형, 1 등
        r"\d+-\d+\.\s*센바\d개\s*\d+bar\s*,\s*\d+", # 5-2.센바1개 350bar, 1 등
        r"\d+\.\s*센서하우징\s*\d+\.\d+\s*,\s*\d+"   # 0.센서하우징 17.92, 1 등
    ]
    
    for pat in ELIMINATE_PATTERNS:
        text = re.sub(pat, ' ', text, flags=re.IGNORECASE)

    # 2. 날짜, 시간, 관리자 정보 삭제 (줄 단위로 깔끔하게)
    text = re.sub(r'.*?(?:Admin|사용자|측정일|오전|오후|\d{1,2}:\d{2}).*?(\n|$)', ' ', text)

    # 3. 추가 키워드 삭제 (ELIMINATE_KEYS)
    combined_eliminate = "|".join([re.escape(kw) for kw in ELIMINATE_KEYS + excluded_keywords])
    text = re.sub(rf'(?:{combined_eliminate})', ' ', text)

    # 4. 수치 데이터 보호 및 기호 정리
    # 구분선(---, ***)은 지우되, 단일 마이너스(-)는 수치 부호이므로 보존 (2개 이상 연속된 것만 삭제)
    text = re.sub(r'[-*_]{2,}', ' ', text)
    # 부호와 숫자 사이 공백 제거 (- 0.001 -> -0.001)
    text = re.sub(r'-\s+(\d+)', r'-\1', text)

    # 5. 키워드 강제 띄어쓰기 (0.020AV= -> 0.020 AV=)
    for key in REQUIRED_KEYS:
        text = re.sub(rf'([\d\.-])({key}=)', r'\1 \2', text)
        text = re.sub(rf'({key}=)([\d\.-])', r'\1 \2', text)

    if debug: print(f"[DEBUG] 전처리 후 텍스트 샘플:\n{text}...")

    # --- [STEP 1] 카테고리 기반 블록 분할 ---
    def  make_flexible_regex(cat_list):
            # 1. 모든 카테고리를 하나의 리스트로 합칩니다.
            all_cats = cat_list
            
            # 2. [핵심] 글자 수(len)가 긴 순서대로 정렬합니다. (위치도 > 위치)
            all_cats.sort(key=len, reverse=True)
            
            # 3. 정규식 패턴 생성
            patterns = [re.escape(cat).replace(r'\ ', r'\s+') for cat in all_cats]
            return "|".join(patterns)   

    cat_pattern = f"({make_flexible_regex(NOMINAL_CATS + TOLERANCE_CATS)})"
    matches = list(re.finditer(cat_pattern, text))
    
    if not matches:
        if debug: print("[DEBUG] 카테고리 매칭 실패!")
        return []

    raw_blocks = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        raw_blocks.append({"cat": matches[i].group(1).strip(), "content": text[start:end].strip()})

    # --- [STEP 2] 부실 블록 합치기 ---
    final_blocks = []
    pending_prefix = ""
    for b in raw_blocks:
        if "=" not in b["content"]:
            pending_prefix = (pending_prefix + " " + b["content"]).strip()
        else:
            if pending_prefix:
                b["content"] = (pending_prefix + " " + b["content"]).strip()
                pending_prefix = ""
            final_blocks.append(b)

    # --- [STEP 3] 데이터 매핑 (숫자 추출 및 할당) ---
    if debug: print(f"\n[DEBUG] --- STEP 3: 매핑 시작 (총 {len(final_blocks)}개 블록) ---")
    
    for idx, b in enumerate(final_blocks):
        cat, content = b["cat"], b["content"]
        
        # 키워드(=)가 처음 등장하는 위치를 기준으로 이름과 데이터를 분리
        data_start_match = re.search(r'(?:NV|UT|LT|TO|DV|AV|XN|YN|ZN|XA|YA|ZA)=', content)
        name_part = content[:data_start_match.start()].strip() if data_start_match else content
        data_part = content[data_start_match.start():].strip() if data_start_match else ""

        # 이름 정제 (하이픈 앞뒤 공백 제거 등)
        name_part = re.sub(r'(\D)\s*-\s*(\d+)', r'\1-\2', name_part)
        final_name = re.sub(r'\s+', ' ', name_part).strip()
        final_name = re.sub(r'^[*-.\s]+|[*-.\s]+$', '', final_name)

        # 데이터 추출 (뒤에서부터 읽어와서 키워드에 할당)
        words = data_part.replace('\n', ' ').split()
        mapping, temp_nums = {}, []
        for i in range(len(words)-1, -1, -1):
            word = words[i].strip()
            if not word: continue
            
            pure_kw = word.rstrip('=')
            if pure_kw in REQUIRED_KEYS:
                if temp_nums:
                    try:
                        mapping[pure_kw] = float(temp_nums.pop(0))
                    except ValueError: continue
                continue
            
            # 숫자 추출: 소수점이 있는 형태만 가져옴 (정수 찌꺼기 방지)
            num_match = re.search(r'-?\d+\.\d+', word)
            if num_match:
                temp_nums.append(num_match.group())

        if debug: print(f"  [Block {idx}] Name: {final_name} | Mapping: {mapping}")

        # 결과 리스트에 담기
        if cat in NOMINAL_CATS:
            results.append(NominalMeasurement(
                name=final_name, cat=cat,
                nv=mapping.get("NV", 0.0), ut=mapping.get("UT", 0.0),
                lt=mapping.get("LT", 0.0), dv=mapping.get("DV", 0.0)
            ))
        else:
            # 공차 항목의 경우 DV가 없으면 ZA, YA, AV 순으로 찾아 할당
            dv_val = mapping.get("DV", mapping.get("ZA", mapping.get("YA", mapping.get("AV", 0.0))))
            results.append(ToleranceMeasurement(
                name=final_name, cat=cat,
                to=mapping.get("TO", 0.0), dv=dv_val
            ))

    return results