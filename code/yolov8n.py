from pathlib import Path
import torch
from ultralytics import YOLO

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data.yaml"
    runs_dir = base_dir / "runs"

    # 1. GPU 설정 확인
    device = '0' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 학습 장치 설정: {device}")

    # 2. 모델 불러오기 (YOLOv8n)
    model = YOLO('yolov8n.pt') 
    
    # 3. 학습 시작
    model.train(
        data=str(data_path),
        
        epochs=100,         # 학습 반복 횟수
        imgsz=640,          # YOLOv8 표준 입력 크기
        batch=16,           # GPU 메모리에 맞춘 배치 사이즈
        device=device,      # GPU 사용
        workers=4,          # 데이터 로딩 워커 수
        
        
        project=str(runs_dir), 
        name='wild_animal_00', 
        exist_ok=True,      
        
        pretrained=True,    
        optimizer='SGD',
        lr0=0.01,
        lrf=0.001,
        momentum=0.937,
        weight_decay=0.001,
        warmup_epochs=5.0,
        warmup_bias_lr=0.05,

        close_mosaic=20,
        degrees=10.0,
        hsv_h=0.03,
        hsv_s=0.9,
        hsv_v=0.5,
        flipud=0.3,
        mixup=0.1,
        copy_paste=0.1,

        dropout=0.1
    )

    print("✅ 학습이 완료되었습니다.")

    best_model_path = runs_dir / 'wild_animal_00' / 'weights' / 'best.pt'
    
    if best_model_path.exists():
        best_model = YOLO(str(best_model_path))
        metrics = best_model.val()
        
        print("-" * 30)
        print(f"🏆 mAP@50-95 (전체 성능): {metrics.box.map:.4f}")    
        print(f"🏆 mAP@50 (IoU 0.5 기준): {metrics.box.map50:.4f}")  
        print("-" * 30)
    else:
        print("⚠️ 학습된 모델 파일을 찾을 수 없습니다.")
