from PIL import Image
import os

# ==========================================
# 🛠️ [설정] 경로를 사원님 환경에 맞게 적어주세요
# ==========================================
input_png_path = "C:/Users/willi/OneDrive/Desktop/AZtech/assets/data/aztech_icon.png" # 원본
output_ico_path = "C:/Users/willi/OneDrive/Desktop/AZtech/assets/data/aztech_icon_opaque.ico" # 덮어쓸 파일

def create_pretty_icon():
    try:
        # 1. 원본 이미지 로드
        img = Image.open(input_png_path).convert("RGBA")
        orig_w, orig_h = img.size

        # 2. 🌟 핵심: 로고 크기를 80%로 줄여서 "여백"을 만듭니다.
        # (원하시면 0.8을 0.85 나 0.9로 조절해서 여백 크기를 바꿀 수 있습니다)
        ratio = 0.8
        new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
        
        # 고화질(LANCZOS) 안티앨리어싱 필터를 써서 예쁘게 축소
        # (과거의 ANTIALIAS 속성이 최신 Pillow에서는 LANCZOS로 변경되었습니다)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. 원본 크기의 '완전한 흰색' 도화지 생성
        white_bg = Image.new("RGB", (orig_w, orig_h), "WHITE")

        # 4. 정중앙에 축소된 로고 배치 (여백이 생김!)
        paste_x = (orig_w - new_w) // 2
        paste_y = (orig_h - new_h) // 2
        
        # 투명한 부분(img_resized의 알파 채널)을 마스크로 써서 부드럽게 합성
        white_bg.paste(img_resized, (paste_x, paste_y), img_resized)

        # 5. 다양한 사이즈로 패키징하여 저장 (윈도우가 상황에 맞춰 골라 씀)
        icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        white_bg.save(output_ico_path, format="ICO", sizes=icon_sizes)
        
        print("✨ [성공] 여백이 추가된 세련된 아이콘이 생성되었습니다!")
        print(f"저장 위치: {output_ico_path}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    create_pretty_icon()