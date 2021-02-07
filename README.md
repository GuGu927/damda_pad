# Wallpad by SKA [SmartKoreAssistant][skorea_link]

![HACS][hacs-shield]
![Version v1.4][version-shield]

Wallpad CustomComponent for Wallpad RS485.<br>
한국의 아파트 홈넷 네트워크(RS485)를 연동하기 위한 CustomComponent.

<br>

## 주의사항
- 본 Component의 사용책임은 전적으로 사용자에게 있습니다.
- 본 Component의 상업적 이용을 하용하지 않습니다.
- 본 Component의 무단배포를 허용하지 않습니다.
- 본문의 내용을 참조할 시 출처를 명시해야합니다.
- 이 외의 내용에 대해서는 제작자에게 문의바랍니다.

<br>


## Version history
| Version | Date        | 내용              |
| :-----: | :---------: | ----------------------- |
| v1.0.0  | 2021.02.07  | First version |

<br>

## Installation
### HACS
- HACS > Integretions > 우측상단 메뉴 > Custom repositories 선택
- 'https://github.com/GuGu927/Wallpad' 주소 입력, Category에 'integration' 선택 후, 저장
- HACS > Integretions 메뉴 선택 후, koreassistant 검색하여 설치

<br>

### 현재 가능한 월패드(최신버전 기준)
- 코콤

<br>

### 지원 예정 월패드
- 코맥스
- 삼성SDS
- CVNET
- 이지빌
- 현대통신

<br>

## Component 기능
| 월패드 | 자동인식 | 상태조회 | 조명 | 난방 | 콘센트 | E/V호출 | 가스차단 | 현관모션 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 코콤 | O | O | O | O | O | O | O | O |
| 코맥스 | O | O | O | O | O | O | O | X |
| 삼성SDS | O | O | O | O | O | X | X | X |

[skorea_link]: https://cafe.naver.com/koreassistant
[version-shield]: https://img.shields.io/badge/version-v1.0.0-orange.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-red.svg
