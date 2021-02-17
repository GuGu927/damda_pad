# Wallpad by SKA [SmartKoreAssistant][skorea_link]

![version](https://img.shields.io/badge/version-1.0-blue)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

CustomComponent for Wallpad.<br>
한국의 아파트 홈넷 네트워크(RS485)의 통합연동 및 호환을 위한 위한 프로그램.<br>
우리집 월패드가 어디껀지 몰라도 알아서 다~~~ 합니다.<br>

## 준비물

- HomeAssistant
- 무선 `Elfin EW11 혹은 TCP/IP 소켓통신이 되는 제품` 혹은 유선 `USB to RS485 컨버터`

## 주의사항

- 월패드의 모든 기능을 이용하려면 각 월패드 업체의 정식 서비스를 이용하시기 바랍니다.
- 본 Component는 각 월패드 업체의 정식 서비스를 이용하지 못하는 사용자에 한해 개인적인 용도로만 사용하기를 권장합니다.
- 본 Component의 사용책임은 전적으로 사용자에게 있습니다.
- 본 Component의 상업적 이용을 하용하지 않습니다.
- 본 Component의 무단배포를 허용하지 않습니다.
- 본문의 내용을 참조할 시 출처를 명시해야합니다.
- 이 외의 내용에 대해서는 제작자에게 문의바랍니다.

<br>

## Version history

| Version |    Date    | 내용    |
| :-----: | :--------: | ------- |
|  v1.0   | 2021.02.xx | Release |

<br>

## Installation

### HACS

- HACS > Integretions > 우측상단 메뉴 > `Custom repositories` 선택
- `https://github.com/GuGu927/SKA-Wallpad` 주소 입력, Category에 `integration` 선택 후, 저장
- HACS > Integretions 메뉴에서 우측 하단 + 누르고 `SKA 월패드` 검색하여 설치
- HomeAssistant 재시작

### Manaul

- `https://github.com/GuGu927/SKA-Wallpad`에서 `custom_components` 폴더를 다운로드, 내부의 `skorea_wallpad` 폴더 확인
- HomeAssistant 설정폴더인 `/config` 에 `custom_components` 폴더를 생성(이미 있으면 다음 단계)
- `/config/custom_components`에 위에서 다운받은 `skorea_wallpad` 폴더를 넣기
- HomeAssistant 재시작

<br>

### 통합구성요소

- HA 사이드패널 > 설정 > 통합 구성요소 > 통합 구성요소 추가
- 검색창에서 `ska wallpad` 입력 후 클릭
- 소켓통신의 경우 `IP 주소`, `포트`를 입력 후 확인
- 씨리얼통신의 경우 씨리얼포트 주소 (ex: `/dev/ttyUSB0`) 입력 후 확인

<br>

### 월패드 설정방법

- **코콤** > 월패드에서 조회 혹은 조작하기

  - 난방 > 상태조회
  - 조명, 대기전력차단 > On/Off 제어
  - 가스차단 > 조회
  - 엘레베이터 > 호출 시 자동인식
  - 환기장치 > 상태조회 혹은 제어
  - 현관모션감지 > 현관 앞에서 움직임

<br>

- **코맥스** > 월패드 자동인식

  - 난방 > 자동인식(패킷 자동추출을 위한 월패드에서 On/Off 제어가 필요할 수 있음.)
  - 조명, 대기전력차단 > 자동인식
  - 가스차단 > 자동인식
  - 엘레베이터 > 현관에서 호출
  - 환기장치 > 자동인식(패킷 자동추출을 위한 월패드에서 On/Off 제어가 필요할 수 있음.)

<br>

- **현대통신** > 월패드에서 조회 혹은 조작하기

  - 난방 > 자동인식
  - 조명, 대기전력차단 > 자동인식
  - 가스차단 > 자동인식
  - 엘레베이터 > 호출 시 자동인식
  - 환기장치 > 자동인식
  - 일괄스위치 -> 자동인식(일괄소등, 가스차단, 방범모드 등 상태조회만 가능.)
  - 원격검침 -> 상태조회

<br>

### 현재 가능한 월패드(최신버전 기준)

|  월패드  | Version |    Date    |
| :------: | :-----: | :--------: |
|   코콤   |  v1.0   | 2021.02.xx |
|  코맥스  |  v1.0   | 2021.02.xx |
| 현대통신 |  v1.0   | 2021.02.xx |

<br>

### 지원 예정 월패드

- 삼성SDS
- CVNET
- 이지빌
- 경동

<br>

## Component 기능

|  월패드  | 자동인식 | 상태조회 | 조명 | 난방 | 콘센트 | E/V호출 | 가스차단 | 일괄소등 | 방범모드 | 현관모션 | 원격검침 |
| :------: | :------: | :------: | :--: | :--: | :----: | :-----: | :------: | :------: | :------: | :------: | :------: |
|   코콤   |    O     |    O     |  O   |  O   |   O    |    O    |    O     |    O     |    X     |    O     |    X     |
|  코맥스  |    O     |    O     |  O   |  O   |   O    |    O    |    O     |    O     |    X     |    X     |    X     |
| 현대통신 |    O     |    O     |  O   |  O   |   O    |    O    |    O     |    O     |    O     |    X     |    O     |

## 오류발생 시 debug 정보 출력방법

- **`configuration.yaml`** 에서 `logger` 항목을 수정<br>

```yaml
logger:
  default: info
  logs:
    custom_components.skorea_wallpad: debug
```

[skorea_link]: https://cafe.naver.com/koreassistant
