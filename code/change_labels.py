import os

# 1. 이미지와 라벨이 들어있는 폴더 경로를 입력하세요.
image_dir = r"C:\Users\Administrator\minji_forder\test\images"
label_dir = r"C:\Users\Administrator\minji_forder\test\labels"

image_files = os.listdir(image_dir)
print("긴 파일명 우회 마법 적용! 이름 변경을 시작합니다...")

count = 0
for img_name in image_files:
    if img_name.lower().endswith(".jpg"):
        
        # 기존 이름 설정
        txt_name = img_name.replace(".jpg", ".txt").replace(".JPG", ".txt")
        old_img_path = os.path.join(image_dir, img_name)
        old_txt_path = os.path.join(label_dir, txt_name)
        
        # '__' 기준으로 자르고 뒷부분만 가져오기
        parts = img_name.split("__")
        new_img_name = parts[-1] 
        new_txt_name = new_img_name.replace(".jpg", ".txt")
        
        # 새로운 전체 경로
        new_img_path = os.path.join(image_dir, new_img_name)
        new_txt_path = os.path.join(label_dir, new_txt_name)
        
        # ✨ 핵심 해결책: 윈도우 260자 제한 우회를 위해 절대 경로 앞에 '\\?\' 붙이기
        long_old_img = "\\\\?\\" + os.path.abspath(old_img_path)
        long_new_img = "\\\\?\\" + os.path.abspath(new_img_path)
        long_old_txt = "\\\\?\\" + os.path.abspath(old_txt_path)
        long_new_txt = "\\\\?\\" + os.path.abspath(new_txt_path)
        
        # 이미지 이름 변경 (이미 바뀐 이름이 아닐 경우)
        if long_old_img != long_new_img:
            os.rename(long_old_img, long_new_img)
            
            # 짝꿍 텍스트 파일도 존재하면 같이 변경 (긴 경로로 확인)
            if os.path.exists(long_old_txt):
                os.rename(long_old_txt, long_new_txt)
            else:
                print(f"⚠️ 텍스트 파일 누락: '{img_name}'의 짝꿍 파일이 없습니다.")
                
            count += 1

print(f"✨ 성공! 윈도우 제한을 뚫고 총 {count}쌍의 파일 이름이 깔끔하게 줄어들었습니다!")