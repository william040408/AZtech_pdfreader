from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Union

@dataclass
class ExcelItem:
    """엑셀의 한 행(Row)에 들어갈 내용을 정의"""
    row_idx: int                         # 엑셀 내 절대적 행 번호 (1, 2, 3...)
    source_type: str = "pdf_idx"         # "pdf_idx", "fixed", "max", "min"
    value_source: Union[int, List[int], str, None] = None 
    label: str = ""                      # 관리용 이름 (ex: "전장", "미측정")

@dataclass
class PartConfig:
    """부품별 측정 설정"""
    name: str                            # 부품 표시 이름
    sub_folder: str                      # 저장될 폴더명
    signature: List[str]                 # PDF 판별용 지문
    data_ranges: List[Tuple[int, Optional[int]]] # 카톡 보고용 범위
    # [ [Item, Item...], [Item, Item...] ] -> 제품 1번용 매핑, 2번용 매핑...
    excel_mapping: List[List[ExcelItem]] = field(default_factory=list)

@dataclass
class RuntimeConfig:
    """프로그램 실행 시 결정되는 환경 설정"""
    machine_name: str                    # "큰 3차원" 등
    base_temp_path: str                  # 서버 루트 경로
    site: str                            # "본관" / "신관"
    machine_numbers: List[int]           # 호기 번호
    stage: str = "초"                    # 초/중/종
    is_night_shift: bool = False         # 주/야간