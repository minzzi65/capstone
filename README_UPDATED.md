# Capstone Project: Wildlife Detection and Deterrent System

## 프로젝트 개요

이 저장소는 YOLO 기반 야생동물 탐지 및 추적/제어 시스템을 구현한 캡스톤 프로젝트입니다. 한국 산림 환경에서 `water_deer`, `wild_boar`, `roe_deer`, `person` 4개 클래스를 탐지하고, 실시간 카메라 추론과 서보/사운드 제어를 통해 사람/동물 분리를 수행합니다.

## 주요 구성

- `code/`
  - `pc_carmera.py`: PC 환경 전용 실행 스크립트입니다. 로컬 웹캠이나 핸드폰 카메라 앱(Iriun 등)을 같은 Wi‑Fi에 연결해 `--source`로 사용합니다. 기본 아두이노 포트는 `COM3`으로 설정되어 있습니다.
  - `webcam.py`: 노트북/웹캠 환경에서 모델 추론 테스트용 스크립트입니다. CLI 인자를 통해 모델 경로와 카메라 소스를 지정할 수 있습니다.
  - `camera.py`: 범용 실시간 추적 스크립트(원래 이름). Windows 환경에서 실행을 염두에 둔 설정과 아두이노 포트 기본값(`COM7`)을 포함합니다.
  - `rasberrypi.py`: 라즈베리파이 전용 실행 스크립트입니다. `picamera2`를 사용해 Pi 카메라에서 프레임을 읽고, 기본적으로 `/dev/ttyACM0` 또는 `/dev/ttyACM1`로 아두이노(또는 마이크로컨트롤러)와 통신합니다. 서보 각도 보정, 안전 범위 및 판별 임계값(기본 0.70)을 포함합니다.
  - `change_labels.py`: YOLOv8 학습 스크립트입니다. `data.yaml`을 사용해 `runs/wild_animal_00` 폴더로 학습 결과를 저장합니다.
  - `test.py`: 학습된 모델을 불러와 테스트 이미지에 대해 탐지 및 결과 저장을 수행합니다. 내부의 `model_path`, `test_images_dir`를 실제 경로로 수정해야 합니다.
  - `data.yaml`: 학습/검증/테스트 데이터셋 경로와 클래스 이름(`water_deer`, `wild_boar`, `roe_deer`, `person`)을 정의합니다.
  - `serial_rasberry_arduino/serial_rasberry_arduino.ino`: 라즈베리파이(또는 PC)에서 전송한 시리얼 명령을 받아 서보(`pan`, `tilt`)와 레이저/버저를 제어하는 Arduino 스케치입니다.
  - `yolov8n.pt`, `yolo26n.pt`: 사전 학습된 가중치 파일들(참고용).

- 최상위 파일
  - `best.pt`: 프로젝트에서 사용 중인 모델 가중치(추론/배포용)로 보입니다.

- 결과 디렉토리
  - `runs/`: 학습 결과 및 평가 정보 저장 디렉토리.
  - `results/`: 탐지 결과와 텍스트 라벨 저장 디렉토리.

## PC(웹캠) vs Raspberry Pi 배포 차이

- PC (파일: `pc_carmera.py`)
  - 로컬 Windows PC 또는 노트북에서 실행하도록 설계되었습니다.
  - 핸드폰을 웹캠으로 사용할 경우 Iriun 같은 앱과 같은 Wi‑Fi에 연결하고, `--source`에 카메라 스트림 URL을 지정하면 사용 가능합니다.
  - 기본 아두이노 포트: `COM3` (환경에 맞게 변경)
  - CPU 모드로 추론하도록 `device='cpu'`를 쓰는 경우도 있어 GPU가 없는 환경에 적합합니다.

- Raspberry Pi (파일: `rasberrypi.py`)
  - Pi 전용 카메라 인터페이스(`picamera2`)를 사용하며, Pi에서 바로 서보 제어 명령을 전송합니다.
  - 아두이노(또는 보드)는 `/dev/ttyACM0` 또는 `/dev/ttyACM1`으로 연결을 시도합니다.
  - 모델 로딩 시 경로와 가중치명을 Pi 환경에 맞춰 수정해야 합니다 (`best_ncnn_model` 같은 파일명 확인 필요).
  - 라즈베리파이에서는 영상 회전, 각도 오프셋, 안전 범위 등이 하드웨어에 맞게 적용되어 있습니다.

## Arduino(스케치) 통합

- 스케치 파일: `code/serial_rasberry_arduino/serial_rasberry_arduino.ino`
  - 시리얼로 `Class,Pan,Tilt\n` 형식의 문자열을 수신합니다. 예: `1,120,45\n`.
  - `OFF` 문자열 수신 시 추적을 중지하고 레이저/버저를 끕니다.
  - 클래스별 동작: `classID`에 따라 버저 주파수 범위를 달리하여 소리를 재생하고, 레이저를 켜거나 끕니다.
  - 부드러운 트래킹을 위해 목표 각도로 서보를 점진 이동시키며, 안전 각도 범위(10°~170°)를 넘지 않도록 제어합니다.

## 데이터셋 정보

- `code/data.yaml`에 설정된 데이터 경로:
  - `train`: `C:\Users\Administrator\minji_forder\dataset__1\train\images`
  - `val`: `C:\Users\Administrator\minji_forder\dataset__1\val\images`
  - `test`: `C:\Users\Administrator\minji_forder\dataset__1\test\images`
- 클래스 수: `4`
- 클래스 이름: `water_deer`, `wild_boar`, `roe_deer`, `person`

## 사용 방법 (요약)

1. 의존성 설치 (예시)

```bash
python -m pip install torch ultralytics opencv-python numpy pyserial
```

2. 학습

```bash
python code/change_labels.py
```

3. PC에서 실시간 테스트 (웹캠 또는 핸드폰 앱)

```bash
python code/pc_carmera.py --source 0 --port COM3 --conf 0.25 --fps 30
# 또는 핸드폰 스트림
python code/pc_carmera.py --source "http://<phone-ip>:8080/video" --port COM3
```

4. Raspberry Pi에서 배포

```bash
python code/rasberrypi.py
```

5. Arduino 플래시: `code/serial_rasberry_arduino/serial_rasberry_arduino.ino`

## 주의 사항

- 여러 스크립트에서 모델 경로가 하드코딩되어 있습니다. 실행 전 `model` 경로를 환경에 맞게 수정하세요.
- PC용(`pc_carmera.py`)은 기본적으로 Windows/CPU 모드 설정이므로 GPU 사용 시 스크립트 내부 인자 확인이 필요합니다.
- 라즈베리파이에서는 `picamera2` 설치와 권한, 그리고 아두이노 포트(`/dev/ttyACM0`) 권한을 확인하세요.

## 요약

이 프로젝트는 PC(웹캠/핸드폰 앱)과 Raspberry Pi 배포 시나리오를 모두 지원하며, 라즈베리파이-아두이노 연동으로 서보/버저/레이저를 제어하는 통합 시스템입니다. `code/` 폴더 내 각 스크립트를 환경에 맞게 수정하여 학습, 테스트, 배포에 활용하세요.
