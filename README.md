# 담다 패드

![version](https://img.shields.io/badge/version-1.0-blue)

- [버전 기록정보](#version-history)
- [주의사항](#주의사항)
- [준비물](#준비물)
- [사용자 구성요소를 HA에 설치하는 방법](#사용자-구성요소를-HA에-설치하는-방법)
  - [HACS](#hacs)
  - [수동설치](#수동설치)
- [담다패드를 통합구성요소로 설치하는 방법](#담다패드를-통합구성요소로-설치하는-방법)
  - [통합구성요소](#통합구성요소)
  - [현재 가능한 제조사(최신버전 기준)](#현재-가능한-제조사최신버전-기준)
  - [지원 예정 제조사](#지원-예정-제조사)
- [담다 패드 버전 정보](#담다-패드-버전-정보)
- [담다 패드 기능](#담다-패드-기능)
- [담다 패드 설정 방법](#담다-패드-설정-방법)
- [오류발생 시 debug 정보 출력방법](#오류발생-시-debug-정보-출력방법)

문의 : 네이버 [HomeAssistant카페](https://cafe.naver.com/koreassistant)

<br/>

## 담다 패드가 도움이 되셨나요?

<a href="https://qr.kakaopay.com/281006011000098177846177" target="_blank"><img src="https://github.com/GuGu927/DAM-Pad/blob/main/images/kakao.png" alt="KaKao"></a>

카카오페이 : https://qr.kakaopay.com/281006011000098177846177

<a href="https://paypal.me/rangee927" target="_blank"><img src="https://www.paypalobjects.com/webstatic/en_US/i/buttons/PP_logo_h_150x38.png" alt="PayPal"></a>

<a href="https://www.buymeacoffee.com/rangee" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee"></a>



## 버전 기록정보

| 버전   | 날짜         | 내용      |
|------|------------|---------|
| v1.0 | 2021.04.xx | 오픈베타 시작 |

<br/>

## 주의사항

- 장치의 모든 기능을 이용하려면 제조사의 정식 서비스를 이용하시기 바랍니다.
- 본 프로그램은 제조사의 정식 서비스를 이용하지 못하는 사용자에 한해 개인적인 용도로만 사용하기를 권장합니다.
- 본 프로그램의 사용책임은 전적으로 사용자에게 있습니다.
- 본 프로그램의 상업적 이용을 하용하지 않습니다.
- 본 프로그램의 무단배포를 허용하지 않습니다.
- 본문의 내용을 참조할 시 출처를 명시해야합니다.
- 처음 사용 시 장치별로 1회 제어하고 장치의 제어가 정상적으로 이루어지지 않을 경우<br/>사용을 즉시 중단하고 `[담다 문의](https://cafe.naver.com/ArticleList.nhn?search.clubid=29860180&search.menuid=89&search.boardtype=L)` 게시판에 글을 남겨주세요.
- 글 작성양식에 맞춰서 작성하고 로그를 같이 첨부해주세요.
- [오류발생 시 debug 정보 출력방법](#오류발생-시-debug-정보-출력방법)
- 특허출원번호 `10-2021-0034748`
- 이 외의 내용에 대해서는 제작자에게 문의바랍니다.

<br/>

## 준비물

- HomeAssistant `최신버전`(**2021.3.4 이상**)
- HomeAssistant OS, Core, Container 등 아무런 상관이 없습니다.
- 무선 `Elfin EW11 혹은 TCP/IP 소켓통신이 되는 제품` 혹은 유선 `USB to RS485 컨버터` 등

<br/>

## 사용자 구성요소를 HA에 설치하는 방법

### HACS(클로즈베타 미지원)

- HACS > Integrations > 우측상단 메뉴 > `Custom repositories` 선택
- `Add custom repository URL`에 `https://github.com/GuGu927/DAM-Pad` 입력
- Category는 `Integration` 선택 후 `ADD` 클릭
- HACS > Integrations 에서 `Damda Pad` 찾아서 설치
- HomeAssistant 재시작

<br/>

### 수동설치

- `담다 자료실`게시판에서 `custom_components` 파일을 다운로드, 내부의 `damda_pad` 폴더 확인
- HomeAssistant 설정폴더인 `/config` 내부에 `custom_components` 폴더를 생성(이미 있으면 다음 단계)<br/>설정폴더는 `configuration.yaml` 파일이 있는 폴더를 의미합니다.<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/folder_config.png)
- `/config/custom_components`에 위에서 다운받은 `damda_pad` 폴더를 넣기<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/folder_custom_component.png)
- HomeAssistant 재시작

<br/>

## 담다패드를 통합구성요소로 설치하는 방법

### 통합구성요소

- HomeAssistant 사이드패널 > 설정 > 통합 구성요소 > 통합 구성요소 추가<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/menu.png)<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/configure.png)<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/integration_add.png)
- 검색창에서 `담다 패드` 입력 후 선택<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/integration_search.png)
- 소켓통신의 경우 `IP 주소`, `포트`를 입력 후 확인
- 씨리얼통신의 경우 씨리얼포트 주소 (ex: `/dev/ttyUSB0`) 입력 후 확인<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/damda_config.png)
- 설치 완료!<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/damda_config_ok.png)
- 만약 자동등록이 되지 않는 경우 담다패드의 `옵션`을 누르고 제조사 선택 후 확인<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/damda_integration_option.png)<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/damda_select_model.png)
- 그 다음 담다패드의 `---`을 누르고 `다시 읽어오기`를 누르면 자동등록 진행<br>![manual_sidebar](https://github.com/GuGu927/DAM-Pad/blob/main/images/damda_reload.png)

<br/>

## 담다 패드 버전 정보

### 현재 지원 가능한 제조사

| 제조사   |  버전  | 날짜         |
|-------|:----:|------------|
| 코콤    | v1.0 | 2021.04.xx |
| 코맥스   | v1.0 | 2021.04.xx |
| 현대통신  | v1.0 | 2021.04.xx |
| 경동원   | v1.0 | 2021.04.xx |
| 이지빌   | v1.0 | 2021.04.xx |
| CVnet | v1.0 | 2021.04.xx |
| 삼성SDS | v1.0 | 2021.04.xx |
| 삼성전자  | v1.0 | 2021.04.xx |
| 그렉스   | v1.0 | 2021.04.xx |
| 에어패스  | v1.0 | 2021.04.xx |
| 정민    | v1.0 | 2021.04.xx |

<br/>

## 담다 패드 기능

| 제조사  | 자동인식 | 제어 | 비고     |
|------|:----:|:--:|--------|
| 삼성전자 |  O   | O  | 시스템에어컨 |
| 그렉스  |  O   | O  | 전열교환기  |
| 에어패스 |  O   | O  | 전열교환기  |
| 정민   |  O   | O  | 전열교환기  |

| 제조사   | 조명 | 디밍 | 콘센트 | 환기 | 보일러 | 에어컨 | 가스차단 | E/V호출 | 일괄소등 | 현관모션 | 일괄스위치 | 원격검침 | 인터폰 |
|-------|:--:|:--:|:---:|:--:|:---:|:---:|:----:|:-----:|:----:|:----:|:-----:|:----:|:---:|
| 코콤    | O  | X  |  O  | O  |  O  |  X  |  O   |   O   |  O   |  O   |   X   |  X   |  X  |
| 코맥스   | O  | X  |  O  | O  |  O  |  X  |  O   |   O   |  O   |  X   |   X   |  X   |  X  |
| 현대통신  | O  | O  |  O  | O  |  O  |  O  |  O   |   O   |  X   |  X   |   O   |  O   |  X  |
| 경동원   | O  | X  |  O  | O  |  O  |  X  |  O   |   O   |  X   |  X   |   O   |  O   |  X  |
| 이지빌   | O  | X  |  O  | X  |  O  |  X  |  O   |   O   |  X   |  X   |   O   |  O   |  X  |
| CVnet | O  | O  |  O  | O  |  O  |  △  |  O   |   O   |  X   |  X   |   O   |  O   |  X  |
| 삼성SDS | O  | X  |  O  | O  |  O  |  X  |  O   |   △   |  X   |  X   |   O   |  O   |  X  |

<br/>

- `일괄소등, 방범모드 등`은 오작동, 스위치 고장 발생, 패킷꼬임, 동거인 컴플레인 등의 문제가 발생할 수 있기에<br/>`상태조회만 지원합니다.`
- △로 표시된 항목은 기능은 구현되어있지만 테스트를 하지 못한 항목입니다.<br/>한번 사용해보고 이상작동 시 담다패드를 비활성화/삭제 하고 `담다 문의` 게시판에 알려주세요.
- X 항목은 베타서비스 중 해당 항목을 보유한 회원이 안계셔서 그렇습니다.<br/>불가능하다는 의미가 아닙니다.
- X 항목이 월패드에서 조회/제어가 된다면 `담다 문의` 게시판에 문의 남겨주세요.(일괄스위치 제외)
- 모든 장치가 등록완료되면 옵션에서 `장치등록`을 비활성화 해주세요.
- `보일러 외출모드`는 HA에서 `송풍모드`로 표시됩니다.
- `가스 스위치`는 가스밸브의 `차단상태`를 의미합니다. 따라서 스위치를 `켜면` 가스밸브를 `차단`합니다.
- 옵션 `모니터링`의 기본값은 비활성화 입니다.<br/>오류가 발생했거나 기능추가를 위해 디버깅을 해야하는 상황이 아니라면 활성화하지 마세요.
- 옵션 `전송간격`의 기본값은 300ms 입니다.<br/>대부분의 경우에서 이 값은 수정하지 않아도 괜찮습니다.<br/>만약 값을 바꿀 경우 너무 낮게 설정하면 문제가 될 수 있습니다.
- 옵션 `엘레베이터 호출`의 기본값은 비활성화 입니다.<br/>만약 이 상태에서 엘레베이터 호출이 되지않다면 활성화 하고, 활성화해도 호출이 안된다면 엘레베이터 호출 스위치는 사용을 중지하세요.
- 옵션 `엘레베이터 시도`의 기본값은 5 입니다.<br/>해당 횟수 만큼 엘레베이터의 호출을 시도합니다.
- 옵션 `중앙난방`의 기본값은 비활성화 입니다.<br/>만약 댁의 난방방식이 중난난방 방식일 경우에만 활성화하세요.
- 옵션 `현관스위치`의 기본값은 비활성화 입니다.<br/>만약 현관스위치의 통신선을 끊었을 경우에만 활성화하세요.

<br/>

## 담다 패드 설정 방법

- **코콤** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > On/Off 제어
  - 난방 > 상태조회
  - 가스차단 > 조회
  - 환기장치 > 상태조회 혹은 제어
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 현관모션감지 > 현관 앞에서 움직임
  - 일괄소등 > On/Off 제어

- **코맥스** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > 자동인식
  - 난방 > 자동인식(추가로 월패드에서 난방/외출 제어가 필요)
  - 가스차단 > 자동인식
  - 환기장치 > 자동인식(추가로 월패드에서 On/Off 제어가 필요)
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(일괄소등, 가스차단, 방범모드 등 `상태조회만` 가능.)

- **현대통신** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > 자동인식
  - 디밍조명 -> 지원예정
  - 난방, 에어컨 > 자동인식
  - 가스차단 > 자동인식
  - 환기장치 > 자동인식
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(일괄소등, 가스차단, 방범모드 등 `상태조회만` 가능.)
  - 원격검침 -> 상태조회 혹은 자동인식

- **경동원** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > 자동인식
  - 난방 > 상태조회 혹은 조작
  - 가스차단 > 자동인식
  - 경동나비엔 에어원 환기장치 -> 자동인식
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(가스차단 등 `상태조회만` 가능.)
  - 원격검침 -> 상태조회 혹은 자동인식

- **이지빌** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > 자동인식
  - 난방 > 상태조회 혹은 조작
  - 가스차단 > 자동인식
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(가스차단 등 `상태조회만` 가능.)
  - 원격검침 -> 상태조회 혹은 자동인식

- **CVnet** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > On/Off 제어
  - 디밍조명 -> 지원예정
  - 난방 > 자동인식
  - 에어컨 > 자동인식`(테스트 필요)`
  - 가스차단 > 자동인식
  - 환기장치 > 자동인식
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(가스밸브상태, 가스누출, 화재감지, 방범모드, 외출모드 등 `상태조회만` 가능.)

- **삼성SDS** > 월패드에서 조회 혹은 조작하기
  - 조명, 대기전력차단 > 자동인식
  - 난방 > 자동인식
  - 가스차단 > 자동인식
  - 환기장치 > 자동인식
  - 엘레베이터 > 자동등록`(미작동시 사용금지)`
  - 일괄스위치 -> 자동인식(일괄소등, 가스차단, 방범모드 등 `상태조회만` 가능.)
  - 인터폰 -> 자동인식`(테스트 필요)`
  - 원격검침 -> 상태조회 혹은 자동인식

- **기타** > 자동인식

<br/>

## 오류발생 시 debug 정보 출력방법

- **`configuration.yaml`** 에서 `logger` 항목을 수정

```yaml
logger:
  default: error
  logs:
    custom_components.damda_pad: debug
```
