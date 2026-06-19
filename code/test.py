from ultralytics import YOLO

def main():
    # 학습된 모델 가중치 경로
    model_path = r"C:\Users\Administrator\minji_forder\runs\wild_animal_00\weights\best.pt"

    # 테스트 이미지들이 들어있는 폴더 경로 (실제 경로로 수정 필요!)
    # data.yaml 기준 경로: dataset3/test/images
    test_images_dir = r"C:\Users\Administrator\minji_forder\Gemini_Generated_Image_.png" 

    # 모델 로드
    model = YOLO(model_path)

    # 추론(Predict) 실행 및 결과 저장
    print("\n=== Test 데이터셋 이미지 탐지 시작 ===")
    results = model.predict(
        source=test_images_dir,
        save=True,         # 바운딩 박스가 그려진 결과 이미지를 저장
        save_txt=True,     # 예측된 좌표와 클래스를 txt 파일로도 저장 (선택)
        save_conf=True,    # txt 파일에 신뢰도(Confidence) 점수 포함 (선택)
        conf=0.8,         # 신뢰도 임계값 (0.25 이상인 객체만 탐지)
        show=False         # 화면에 바로 이미지를 띄울지 여부 (이미지가 많으므로 False 권장)
    )
    
    print("\n=== 탐지 완료! ===")
    print("결과 이미지는 터미널 창에 출력된 'Results saved to runs/detect/predict...' 경로에서 확인할 수 있습니다.")

if __name__ == "__main__":
    main()
