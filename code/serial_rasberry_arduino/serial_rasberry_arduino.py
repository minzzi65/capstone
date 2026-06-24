#include <Servo.h>

Servo panServo;
Servo tiltServo;

const int laserPin = 8;    
const int panPin = 9;      
const int tiltPin = 10;    
const int buzzerPin = 11;  

// 시작 시 초기값 90도 (정중앙)
float currentPan = 90.0;
float currentTilt = 90.0;
float targetPan = 90.0;
float targetTilt = 90.0;

float lastValidPan = 90.0;
float lastValidTilt = 90.0;

const int minAngle = 10;
const int maxAngle = 170;

// 부드러운 움직임을 위한 속도 제어 변수
const float trackingSpeed = 0.22; 

bool trackingMode = false; 

// ⭐ 랜덤 소리 변환 주기를 제어하기 위한 시간 변수
unsigned long lastSoundUpdateTime = 0;
const unsigned long soundInterval = 500; // 500ms(0.5초) 마다 랜덤 주파수 변경 (원하는 대로 조절 가능)

void setup() {
  Serial.begin(9600); 
  
  pinMode(laserPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  
  digitalWrite(laserPin, LOW); 
  noTone(buzzerPin);
  
  panServo.attach(panPin);
  tiltServo.attach(tiltPin);
  
  panServo.write((int)currentPan);
  tiltServo.write((int)currentTilt);
}

void loop() {
  if (Serial.available() > 0) {
    String rpiData = Serial.readStringUntil('\n');
    rpiData.trim();

    if (rpiData == "OFF") {
      trackingMode = false;
    } 
    else if (rpiData.length() > 0) {
      int firstComma = rpiData.indexOf(',');
      int secondComma = rpiData.indexOf(',', firstComma + 1);

      if (firstComma != -1 && secondComma != -1) {
        int classID = rpiData.substring(0, firstComma).toInt();
        int inPan = rpiData.substring(firstComma + 1, secondComma).toInt();
        int inTilt = rpiData.substring(secondComma + 1).toInt();
        
        if (classID == 3) {
          trackingMode = false;
        } 
        else if (classID == 0 || classID == 1 || classID == 2) {
          targetPan = inPan;
          targetTilt = inTilt;
          
          lastValidPan = targetPan;
          lastValidTilt = targetTilt;
          
          trackingMode = true; 

          // ⭐ [수정] 지정한 시간(soundInterval)이 지났을 때만 랜덤 주파수를 갱신합니다.
          if (millis() - lastSoundUpdateTime >= soundInterval) {
            lastSoundUpdateTime = millis(); // 시간 동기화

            if (classID == 0 || classID == 2) {
              // 고라니, 노루: 초음파 대역 랜덤 출력 (18kHz~25kHz)
              int randomFreq = random(18000, 25000); 
              tone(buzzerPin, randomFreq);
            }
            else if (classID == 1) {
              // 멧돼지: 위협적인 가청음 대역 랜덤 출력 (2kHz~8kHz)
              int randomFreq = random(2000, 8000); 
              tone(buzzerPin, randomFreq);
            }
          }
        }
      }
    }
  }

  // 모드에 따른 출력 제어
  if (!trackingMode) {
    targetPan = lastValidPan;
    targetTilt = lastValidTilt;
    
    digitalWrite(laserPin, LOW);
    noTone(buzzerPin);
  } 
  else {
    digitalWrite(laserPin, HIGH);
  }

  // 목표 각도로 부드럽게 이동
  currentPan += (targetPan - currentPan) * trackingSpeed;
  currentTilt += (targetTilt - currentTilt) * trackingSpeed;

  currentPan = constrain(currentPan, minAngle, maxAngle);
  currentTilt = constrain(currentTilt, minAngle, maxAngle);

  panServo.write((int)currentPan);
  tiltServo.write((int)currentTilt);

  // ⭐ [수정] 메인 루프 지연 시간을 50ms로 늘려 모터와 통신을 안정화합니다.
  delay(50); 
}