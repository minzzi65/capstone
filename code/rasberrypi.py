import cv2
import serial
import time
from ultralytics import YOLO
from picamera2 import Picamera2

# =====================================================================
# ⚙️ [하드웨어 영점 및 오프셋 튜닝 변수]
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

# 1. 아두이노 시리얼 통신 연결
try:
    arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=1)
    time.sleep(2)
    print("🟢 아두이노 연결 성공! (/dev/ttyACM0)")
except:
    try:
        arduino = serial.Serial(port='/dev/ttyACM1', baudrate=9600, timeout=1)
        time.sleep(2)
        print("🟢 아두이노 연결 성공! (/dev/ttyACM1)")
    except:
        print("❌ 아두이노 연결 실패 - 포트를 확인해주세요.")

# 2. YOLO 모델 및 카메라 초기화
model = YOLO("best_ncnn_model", task="detect") # 최적화된 가중치 파일명 확인

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

print("🚀 스마트 야생동물 추적 AI 엔진 가동 중...")

# 초기 대기 상태 위치 세팅
last_valid_pan = 90
last_valid_tilt = 130

while True:
    try:
        # 📸 카메라 프레임 획득 (정방향 180도 회전 포함)
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # AI 모델 추론 (터미널 로그 과부하 방지를 위해 verbose=False)
        results = model(frame, imgsz=640, verbose=False)
        annotated_frame = results[0].plot()

        boxes = results[0].boxes

        if len(boxes) > 0:
            box = boxes[0] 
            
            # 💡 클래스 ID와 탐지 신뢰도(Confidence) 추출
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())

            # 💡 1차 논리 검증: 정확도가 70% 이상일 때만 제어 명령 생성
            if confidence >= 0.70:
                xywhn = box.xywhn[0].tolist()
                center_x = xywhn[0]
                center_y = xywhn[1]

                # 🎯 [수평 축 - Pan] 화면 정중앙(0.5) 기준 90도 기저값 적용
                if INVERT_PAN:
                    base_pan = 90 + ((center_x - 0.5) * TRAVEL_RANGE_PAN)
                else:
                    base_pan = 90 - ((center_x - 0.5) * TRAVEL_RANGE_PAN)

                # 🎯 [수직 축 - Tilt 핵심 보정] 기저 시작 각도 40도
                if INVERT_TILT:
                    base_tilt = 40 - ((center_y - 0.5) * TRAVEL_RANGE_TILT)
                else:
                    base_tilt = 40 + ((center_y - 0.5) * TRAVEL_RANGE_TILT)

                # 🛠️ 최종 영점 오프셋 적용
                final_pan = base_pan + OFFSET_PAN
                final_tilt = base_tilt + OFFSET_TILT

                # 서보모터 하드웨어 제어 가동 범위 제한 (10~170도 소프트웨어 안전 마진)
                final_pan = max(10, min(170, final_pan))
                final_tilt = max(10, min(170, final_tilt))

                last_valid_pan = final_pan
                last_valid_tilt = final_tilt

                # 🚀 클래스 ID, Pan, Tilt 순서로 통신 규격에 맞춰 전송
                if 'arduino' in globals() and arduino.is_open:
                    cmd = f"{class_id},{int(final_pan)},{int(final_tilt)}\n"
                    arduino.write(cmd.encode())
                    arduino.flush() 

                print(f"🎯 절대 조준 중 -> Class:{class_id}, Conf:{confidence:.2f}, Pan:{int(final_pan)}°, Tilt:{int(final_tilt)}°")
            
            else:
                # 70% 미만의 불확실한 객체는 오작동 방지를 위해 정지
                if 'arduino' in globals() and arduino.is_open:
                    arduino.write("OFF\n".encode())
                print(f"⚠️ 정확도 미달 ({confidence:.2f}) -> 대기 중")

        else:
            # 타겟 미탐지 시 정지 신호 전송
            if 'arduino' in globals() and arduino.is_open:
                arduino.write("OFF\n".encode())
            print(f"💤 미탐지 (마지막 위치 대기) -> Pan:{int(last_valid_pan)}°, Tilt:{int(last_valid_tilt)}°")

        # 📺 실시간 모니터링 창 출력
        cv2.namedWindow("YOLOv8 Real-Time Wildlife Deterrent", cv2.WINDOW_NORMAL)
        cv2.imshow("YOLOv8 Real-Time Wildlife Deterrent", annotated_frame)

        # 50ms 대기 (q 키 누르면 종료)
        if cv2.waitKey(50) & 0xFF == ord("q"):
            break

    except KeyboardInterrupt:
        print("\n👋 사용자가 종료를 요청했습니다.")
        break
    except Exception as e:
        print(f"⚠️ 에러 발생: {e}")
        break

# 시스템 안전 종료
picam2.stop()
if 'arduino' in globals() and arduino.is_open:
    arduino.close()
cv2.destroyAllWindows()