import cv2
import argparse
import os
import time
import numpy as np

# 1. 윈도우 환경 YOLO/PyTorch 충돌(프리징) 완벽 방지
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

from ultralytics import YOLO

# 아두이노 연결을 위한 시리얼 라이브러리
try:
    import serial
except ImportError:
    serial = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='0', help='카메라 번호')
    parser.add_argument('--port', type=str, default='COM3', help='아두이노 포트')
    parser.add_argument('--conf', type=float, default=0.25, help='AI 인식 정확도 기준')
    parser.add_argument('--fps', type=int, default=30, help='초당 프레임 수')
    args = parser.parse_args()

    # [아두이노 연결]
    if serial:
        try:
            ser = serial.Serial(args.port, 9600)
            print(f"아두이노와 연결되었습니다. 포트: {args.port}")
        except Exception as e:
            print(f"아두이노 연결 실패 (계속 진행합니다): {e}")
            ser = None
    else:
        ser = None

    # ★ [AI 모델 로드] 말씀해주신 절대 경로 적용 (r을 붙여 경로 에러 방지)
    print("AI 모델을 불러오는 중입니다...")
    model_path = r"C:\Users\Administrator\pill\best.pt"
    model = YOLO(model_path) 

    # ★ 핵심 1: 카메라를 켜기 전에 AI 워밍업부터 무조건 끝냄 (카메라 튕김 방지)
    print("AI 모델 초기 워밍업 중입니다 (최대 1~2분 소요. 가만히 기다려주세요)...")
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    model.predict(source=dummy_frame, device='cpu', show=False, verbose=False)
    print("AI 워밍업 완료! 본격적인 실시간 추적을 시작합니다.")

    # ★ 핵심 2: 워밍업 직후에 카메라 연결 (지연 없이 바로 연결됨)
    source_val = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source_val)

    if not cap.isOpened():
        print("에러: 카메라를 열 수 없습니다. 핸드폰 Iriun 앱이 켜져 있는지 확인하세요!")
        return

    print("카메라가 켜졌습니다. 종료하려면 영상 창에서 'q'를 누르세요.")

    # 화면 창을 맨 앞으로 강제 고정 (뒤에 숨는 것 방지)
    cv2.namedWindow("Wildlife Detection Test", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Wildlife Detection Test", cv2.WND_PROP_TOPMOST, 1)

    frame_interval = 1.0 / args.fps if args.fps > 0 else 0.0
    last_shown = 0.0

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("프레임을 읽어올 수 없습니다. 카메라 연결이 끊겼습니다.")
            break
            
        now = time.time()
        if frame_interval > 0 and (now - last_shown) < frame_interval:
            continue
        last_shown = now

        # 프레임 크기 강제 축소 (과부하 방지)
        frame = cv2.resize(frame, (640, 480))

        # AI 실시간 분석 (device='cpu'로 그래픽카드 에러 무시)
        results = model.predict(source=frame, conf=args.conf, show=False, verbose=False, device='cpu')
        
        # 사진에 네모 박스 그리기
        annotated_frame = results[0].plot()

        # 화면에 띄우기
        cv2.imshow("Wildlife Detection Test", annotated_frame)

        # ★ 핵심 3: 윈도우 창 숨쉬기 (이게 있어야 '응답 없음' 안 뜸)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 종료 시 자원 반납
    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()

if __name__ == '__main__':
    main()