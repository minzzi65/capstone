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

# =====================================================================
# ⚙️ [하드웨어 영점 및 오프셋 튜닝 변수] - 라즈베리파이 설정 그대로 이식
# =====================================================================
INVERT_PAN = False   # 동물의 움직임과 모터가 반대로 도망가면 True로 변경
INVERT_TILT = False  # 동물의 움직임과 모터가 반대로 도망가면 True로 변경

# 🎯 서보 모터의 최대 활동 반경 (화면 끝으로 갈 때 움직일 각도 범위)
TRAVEL_RANGE_PAN = 60   
TRAVEL_RANGE_TILT = 40  

# 🛠️ [영점 보정 반영] 락(Lock)이 안 걸리는 마진 구조 세팅
OFFSET_PAN = -50
OFFSET_TILT = -30      
# =====================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='0', help='카메라 번호')
    parser.add_argument('--port', type=str, default='COM7', help='아두이노 포트')
    parser.add_argument('--conf', type=float, default=0.70, help='AI 인식 정확도 기준 (기본 70%)')
    parser.add_argument('--fps', type=int, default=30, help='초당 프레임 수')
    args = parser.parse_args()

    # [아두이노 연결]
    if serial:
        try:
            # write_timeout 설정을 넣어 데이터 전송 밀림으로 인한 응답없음을 완전히 예방합니다.
            ser = serial.Serial(args.port, 9600, timeout=1, write_timeout=0.05)
            time.sleep(2) # 아두이노 부팅 대기
            print(f"🟢 아두이노 연결 성공! 포트: {args.port}")
        except Exception as e:
            print(f"❌ 아두이노 연결 실패 (하드웨어 없이 AI 화면만 테스트합니다): {e}")
            ser = None
    else:
        ser = None

    # [AI 모델 로드] 지정해주신 절대 경로 적용
    print("AI 모델을 불러오는 중입니다...")
    model_path = r"C:\Users\Administrator\pill\best.pt"
    model = YOLO(model_path) 

    # AI 초기 워밍업 (카메라 튕김 방지)
    print("AI 모델 초기 워밍업 중입니다...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    model.predict(source=dummy_frame, device='cpu', show=False, verbose=False)
    print("🚀 스마트 야생동물 추적 AI 엔진 가동 중...")

    # 카메라 연결 (Iriun 웹캠 등)
    source_val = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source_val)

    if not cap.isOpened():
        print("에러: 카메라를 열 수 없습니다. 핸드폰 Iriun 앱이 켜져 있는지 확인하세요!")
        return

    print("카메라가 켜졌습니다. 종료하려면 영상 창에서 'q'를 누르세요.")

    # 화면 창 맨 앞으로 고정
    cv2.namedWindow("YOLOv8 Real-Time Wildlife Deterrent", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("YOLOv8 Real-Time Wildlife Deterrent", cv2.WND_PROP_TOPMOST, 1)

    frame_interval = 1.0 / args.fps if args.fps > 0 else 0.0
    last_shown = 0.0

    # 초기 대기 상태 위치 세팅 (라즈베리파이 값 적용)
    last_valid_pan = 90
    last_valid_tilt = 130
    
    # 아두이노 통신 폭주 및 버퍼 프리징 방지용 플래그
    tracking_active = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽어올 수 없습니다. 카메라 연결이 끊겼습니다.")
            break
            
        now = time.time()
        if frame_interval > 0 and (now - last_shown) < frame_interval:
            continue
        last_shown = now

        # 아두이노 좌표 일치를 위해 640x480 해상도 고정 
        # (웹캠은 정방향이므로 라즈베리파이에 있던 ROTATE_180 회전 코드는 제외했습니다)
        frame = cv2.resize(frame, (640, 480))

        # AI 실시간 분석 (터미널 과부하 방지를 위해 verbose=False)
        results = model.predict(source=frame, imgsz=640, show=False, verbose=False, device='cpu')
        annotated_frame = results[0].plot()
        boxes = results[0].boxes
        
        # ================= [★ 라즈베리파이 수학 공식 및 터미널 출력 이식] =================
        if len(boxes) > 0:
            box = boxes[0] 
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            
            # 💡 설정한 정확도 기준(기본 70%) 이상일 때만 제어 명령 생성
            if confidence >= args.conf:
                xywhn = box.xywhn[0].tolist()
                center_x = xywhn[0]
                center_y = xywhn[1]
                
                # 🎯 [수평 축 - Pan] 화면 정중앙(0.5) 기준 90도 기저값 적용
                if INVERT_PAN:
                    base_pan = 90 + ((center_x - 0.5) * TRAVEL_RANGE_PAN)
                else:
                    base_pan = 90 - ((center_x - 0.5) * TRAVEL_RANGE_PAN)
                    
                # 🎯 [수직 축 - Tilt] 기저 시작 각도 40도 적용
                if INVERT_TILT:
                    base_tilt = 40 - ((center_y - 0.5) * TRAVEL_RANGE_TILT)
                else:
                    base_tilt = 40 + ((center_y - 0.5) * TRAVEL_RANGE_TILT)
                    
                # 🛠️ 최종 영점 오프셋 적용
                final_pan = base_pan + OFFSET_PAN
                final_tilt = base_tilt + OFFSET_TILT
                
                # 하드웨어 안전 마진 적용 (10~170도 범위 제한)
                final_pan = max(10, min(170, final_pan))
                final_tilt = max(10, min(170, final_tilt))
                
                last_valid_pan = final_pan
                last_valid_tilt = final_tilt
                
                # 아두이노로 데이터 송신
                if ser and ser.is_open:
                    cmd = f"{class_id},{int(final_pan)},{int(final_tilt)}\n"
                    try:
                        ser.write(cmd.encode())
                        ser.flush()
                    except serial.SerialTimeoutException:
                        pass
                
                # 🎯 터미널 창 실시간 출력
                print(f"🎯 절대 조준 중 -> Class:{class_id}, Conf:{confidence:.2f}, Pan:{int(final_pan)}°, Tilt:{int(final_tilt)}°")
                tracking_active = True
                
            else:
                # 정확도 미달 시 정지 신호 안전 전송
                if tracking_active and ser and ser.is_open:
                    try: ser.write(b"OFF\n")
                    except serial.SerialTimeoutException: pass
                    tracking_active = False
                
                # ⚠️ 터미널 창 실시간 출력
                print(f"⚠️ 정확도 미달 ({confidence:.2f}) -> 대기 중")
        else:
            # 타겟 미탐지 시 정지 신호 안전 전송
            if tracking_active and ser and ser.is_open:
                try: ser.write(b"OFF\n")
                except serial.SerialTimeoutException: pass
                tracking_active = False
                
            # 💤 터미널 창 실시간 출력
            print(f"💤 미탐지 (마지막 위치 대기) -> Pan:{int(last_valid_pan)}°, Tilt:{int(last_valid_tilt)}°")
        # =========================================================================

        # 화면 출력
        cv2.imshow("YOLOv8 Real-Time Wildlife Deterrent", annotated_frame)

        # 키보드 'q' 누르면 안전 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 자원 반납
    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()

if __name__ == '__main__':
    main()