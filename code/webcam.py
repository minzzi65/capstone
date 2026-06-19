import cv2
import argparse
import os
import time
from ultralytics import YOLO

def parse_args():
    parser = argparse.ArgumentParser(description="YOLO webcam inference for laptop/Raspberry Pi")
    parser.add_argument(
        "--model",
        default=r"C:\Users\Administrator\pill\best.pt",
        help="Model path (ex: best.onnx or best.pt)",
    )
    parser.add_argument(
        "--source",
        default="0",
        help="Camera source. ex) 0 (USB cam) or http://<phone-ip>:8080/video",
    )
    parser.add_argument("--conf", type=float, default=0.7, help="Confidence threshold (default: 0.7)")
    parser.add_argument("--fps", type=float, default=10.0, help="Display FPS limit (default: 10)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.model):
        print(f"모델 파일을 찾을 수 없습니다: {args.model}")
        print("예: python webcam.py --model /home/pi/models/best.onnx")
        return

    model = YOLO(args.model)

    # Windows에서는 CAP_DSHOW가 카메라 오픈 안정성에 도움이 되고,
    # Linux(라즈베리파이/노트북)에서는 기본 백엔드를 사용합니다.
    source = int(args.source) if args.source.isdigit() else args.source
    if os.name == "nt" and isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"카메라를 열 수 없습니다. source={args.source} 확인해 주세요.")
        return

    print("카메라가 켜졌습니다. 종료하려면 영상 창에서 'q'를 누르세요.")
    print(f"사용 모델: {args.model}")
    print(f"입력 소스: {args.source}")

    frame_interval = 1.0 / args.fps if args.fps > 0 else 0.0
    last_shown = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽어올 수 없습니다.")
            break

        # 표시 속도 제한으로 화면이 너무 빨리 바뀌는 현상을 줄입니다.
        now = time.time()
        if frame_interval > 0 and now - last_shown < frame_interval:
            continue
        last_shown = now

        results = model.predict(source=frame, conf=args.conf, show=False, verbose=False)
        result = results[0]
        names = result.names
        # 화면에는 이름만 표시(신뢰도/conf는 숨김)
        annotated_frame = result.plot(conf=False)

        boxes = result.boxes
        if boxes is not None and boxes.xyxy is not None and boxes.cls is not None:
            xyxy = boxes.xyxy.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy().astype(int)
            for i, box in enumerate(xyxy):
                x1, y1, x2, y2 = [int(v) for v in box[:4]]
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                cls_id = int(cls_ids[i])
                cls_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(names[cls_id])

                # 터미널에는 객체 ID + 좌표 출력
                print(f"id={cls_id} name={cls_name} box=({x1},{y1},{x2},{y2}) center=({cx},{cy})")

        cv2.imshow("Wildlife Detection Test", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
