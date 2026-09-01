# seethrough


## E2E/UI/UX TEST pytest 실행 방법

| 실행 목적 | 명령어 또는 옵션 |
| --- | --- |
| 전체 실행 | `pytest` |
| 상세 실행 결과 표시 | `-v` |
| 브라우저 표시 | `--headed` |
| 실행 속도 조절 | `--slowmo 500` |
| 마커 사용 | `-m <marker명>` |

```bash
각 E2E 흐름은 브라우저 상태를 공유하므로 개별 ID만 실행하지 않는다.
-x, --maxfail=1, pytest-xdist의 -n 옵션을 사용하지 않는다.
```

### marker로 실행

```powershell
pytest -m exam_flow -v
pytest -m board_flow -v
pytest -m schedule_flow -v
pytest -m exam_retake_flow -v
pytest -m schedule_management_flow -v
pytest -m exam_status_flow -v
pytest -m exam_multi -v
pytest -m exam_auto_save -v
pytest -m board_offline -v
pytest -m board_duplicate -v
pytest -m board_title_limit -v
pytest -m exam_offline -v
```

| Marker | TC ID | 테스트 흐름 |
| --- | --- | --- |
| `exam_flow` | ID 1~15 | 시험 응시 |
| `board_flow` | ID 16~20 | 게시판 |
| `schedule_flow` | ID 21~23 | 수업 일정 |
| `exam_retake_flow` | ID 24~26 | 시험 재응시 |
| `schedule_management_flow` | ID 27~35 | 수업 일정 관리 |
| `exam_status_flow` | ID 36~40 | 시험 응시 현황 |
| `exam_multi` | ID 41 | 다중 탭 시험 |
| `exam_auto_save` | ID 42 | 답안 자동 저장 |
| `board_offline` | ID 43~44 | 네트워크 중단 게시물 저장 검증 |
| `board_duplicate` | ID 45 | 게시물 중복 요청 검증 |
| `board_title_limit` | ID 46 | 게시물 제목 글자 수 제한 검증 |
| `exam_offline` | ID 47 | 네트워크 중단 시험 문제 불러오기 검증 |

### 브라우저 표시 및 실행 속도 조절

```powershell
pytest -m exam_flow -v --headed
pytest -m exam_flow -v --headed --slowmo 500
```

- `--headed`: 브라우저를 화면에 표시함
- `--slowmo 500`: Playwright 동작마다 500ms 지연함

### Allure 결과 생성

```powershell
pytest -v --alluredir allure-results --clean-alluredir
```
전체 TC를 ID 순서로 실행하면서 Allure 결과를 생성하려면 다음 명령어를 사용한다.

### Allure 보고서 열기

```powershell
allure serve allure-results
```
