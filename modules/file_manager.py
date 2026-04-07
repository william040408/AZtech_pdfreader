import os
import shutil
from typing import List, Dict
import time

class FileManager:
    def __init__(self):
        self.base_path = ""

    def set_base_path(self, path: str):
        # 경로가 절대 경로인지 확인하고 설정
        self.base_path = os.path.abspath(path)

    def _get_unique_path(self, target_path: str) -> str:
        """파일이 이미 존재하면 이름 뒤에 (1), (2) 등을 붙여 고유한 경로를 반환합니다."""
        if not os.path.exists(target_path):
            return target_path

        base, ext = os.path.splitext(target_path)
        counter = 1
        while True:
            new_path = f"{base} ({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def _generate_new_name(self, part_config: Dict, measurements: List, 
                           site: str, machines: List[int], timing: int, 
                           tool_changes: List[bool]) -> str:
        
        part_name = part_config.get("name", "알수없는부품")
        ranges = part_config.get("data_ranges", [])
        
        # 1. 센서바디 규칙 (멀티 부품 대응)
        if "센서바디" in part_name:
            machine_parts = []
            for i, r in enumerate(ranges):
                start, end = r
                # ⚠️ 핵심 수정: measurements 리스트 범위를 벗어나지 않도록 체크
                target_measurements = measurements[start : end + 1]
                
                # ⚠️ 핵심 수정: m.is_ng 가 메서드인지 속성인지 확인 후 호출
                # 윌리엄님의 Measurement 클래스 구조에 맞게 수정 (메서드라면 () 필요)
                has_ng = False
                for m in target_measurements:
                    try:
                        if callable(m.is_ng):
                            if m.is_ng(): has_ng = True; break
                        elif m.is_ng: # 속성일 경우
                            has_ng = True; break
                    except: continue

                n_suffix = "n" if has_ng else ""
                is_t = tool_changes[i] if i < len(tool_changes) else False
                t_suffix = "T" if is_t else ""
                current_m_no = machines[i] if i < len(machines) else (machines[0] if machines else "?")
                
                machine_parts.append(f"{current_m_no}{t_suffix}{n_suffix}")
            
            machine_str = ".".join(machine_parts)
            return f"{site} 센서바디 {machine_str}-{timing}.pdf"

        # 2. 기타 부품들 (다이아 프램, 센서하우징 등)
        else:
            m_no = machines[0] if machines else "?"
            is_t = tool_changes[0] if tool_changes else False
            t_suffix = "T" if is_t else ""
            
            has_ng = False
            for m in measurements:
                try:
                    if callable(m.is_ng):
                        if m.is_ng(): has_ng = True; break
                    elif m.is_ng:
                        has_ng = True; break
                except: continue
                
            n_suffix = "n" if has_ng else ""
            
            if "다이아 프램" in part_name:
                face = part_config.get("face", "정면")
                return f"다이아 프램 {m_no}-{timing}{t_suffix} {face}{n_suffix}.pdf"
            
            combined_suffix = f"{t_suffix}{n_suffix}"
            if "센서하우징" in part_name:
                size = "17.92" if "17.92" in part_name else "19.25"
                return f"센서하우징 {m_no}-{timing}{combined_suffix} {size}.pdf"
            
            if "ACV" in part_name:
                time_lst = ['초품', '중품', '종품']
                return f"{time_lst[timing-1]}.pdf"

            else:
                return f"{m_no}-{timing}{combined_suffix}.pdf"

    def move_and_save(self, temp_pdf_path: str, part_config: Dict, measurements: List, 
                      site: str, machines: List[int], timing: int, 
                      tool_changes: List[bool], mode: str = 'copy'):
        
        # 1. 파일명 생성 시도
        try:
            new_filename = self._generate_new_name(part_config, measurements, site, machines, timing, tool_changes)
        except Exception as e:
            print(f"❌ 파일명 생성 실패: {e}")
            new_filename = f"ERROR_RENAME_{int(time.time())}.pdf"

        # 2. 경로 설정
        sub_folder = part_config.get("sub_folder", "기타")
        target_dir = os.path.join(self.base_path, sub_folder)
        
        # 3. 폴더 생성 (이미 있으면 무시)
        os.makedirs(target_dir, exist_ok=True)
            
        initial_target_path = os.path.join(target_dir, new_filename)
        final_target_path = self._get_unique_path(initial_target_path)

        # 4. 파일 이동/복사 실행
        try:
            if mode == 'copy':
                shutil.copy2(temp_pdf_path, final_target_path)
            else:
                shutil.move(temp_pdf_path, final_target_path)
            
            print(f"📁 [{mode.upper()} 성공] {final_target_path}")
            return final_target_path
        except Exception as e:
            print(f"❌ 파일 조작 실패: {e}")
            return None