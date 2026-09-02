# seethrough QA 자동화

Elice LXP QA 환경의 E2E/UI/UX 테스트를 Playwright와 pytest로 실행합니다.

## 기본 실행

| 목적 | 명령어 |
| --- | --- |
| 전체 테스트 | `pytest` |
| 상세 결과 표시 | `pytest -v` |
| 브라우저 표시 | `pytest --headed` |
| 동작 지연 추가 | `pytest --slowmo 500` |
| 특정 marker 실행 | `pytest -m <marker명>` |

각 E2E 흐름은 브라우저 상태를 공유하므로 개별 ID만 단독 실행하지 않습니다. 테스트 간 상태 충돌을 방지하기 위해 `pytest-xdist` 병렬 실행(`-n`)도 사용하지 않습니다.

## Marker별 실행

| Marker | TC ID | 테스트 흐름 |
| --- | --- | --- |
| `exam_flow` | ID 1~15 | 시험 응시 및 제출 |
| `board_flow` | ID 16~20 | 게시판 기본 흐름 |
| `schedule_flow` | ID 21~23 | 수업 일정 조회 |
| `exam_retake_flow` | ID 24~26 | 시험 재응시 |
| `schedule_management_flow` | ID 27~35 | 수업 일정 관리 |
| `exam_status_flow` | ID 36~40 | 시험 응시 현황 |
| `exam_multi` | ID 41 | 다중 탭 시험 |
| `exam_refresh_save` | ID 42 | 새로고침 후 답안 저장 |
| `board_offline` | ID 43~44 | 네트워크 중단 게시물 저장 |
| `board_duplicate` | ID 45 | 게시물 중복 요청 |
| `board_title_limit` | ID 46 | 게시물 제목 글자 수 제한 |
| `exam_offline` | ID 47 | 네트워크 중단 시험 문제 불러오기 |
| `exam_timeout` | ID 48 | 제한 시간 종료 |
| `invalid_url` | ID 49 | 존재하지 않는 URL 접근 |
| `responsive_layout` | ID 50~53 | 반응형 메뉴 |
| `mocking500` | ID 54 | 클래스 조회 API 500 Mock |

예시:

```powershell
pytest -m exam_flow -v
pytest -m responsive_layout -v --headed
pytest -m exam_refresh_save -v
pytest -m mocking500 -v
```

## 영상 녹화

| 목적 | 명령어 |
| --- | --- |
| 특정 흐름 전체 녹화 | `pytest -m exam_flow -v --video=on` |
| 전체 테스트 녹화 | `pytest -v --headed --video=on` |
| 실패한 흐름만 보존 | `pytest -v --video=retain-on-failure` |

영상은 `videos/<테스트 파일명>/` 아래에 저장됩니다. `retain-on-failure`는 한 흐름 안에서 테스트 하나라도 실패하면 해당 흐름 전체 영상을 보존합니다.

## Allure 리포트

```powershell
pytest -v --alluredir allure-results --clean-alluredir
allure serve allure-results
```

첫 번째 명령어로 결과를 생성하고, 두 번째 명령어로 로컬 리포트를 엽니다.
