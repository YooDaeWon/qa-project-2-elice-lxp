# seethrough

## 기본 실행

| 목적 | 명령어 |
| --- | --- |
| 전체 테스트 | `pytest` |
| 상세 결과 표시 | `pytest -v` |
| 브라우저 표시 | `pytest --headed` |
| 동작 지연 추가 | `pytest --slowmo 500` |
| 특정 marker 실행 | `pytest -m <marker명>` |

각 E2E 흐름은 브라우저 상태를 공유하므로 개별 ID만 단독 실행하지 않습니다.  
테스트 간 상태 충돌을 방지하기 위해 `pytest-xdist` 병렬 실행(`-n`)도 사용하지 않습니다.

## Safety Design

지정된 QA 트랙 Dev 기관(`dev-qatrack`) 안에서만 실행합니다. 운영 서비스와 타 과목은 대상이 아닙니다.

기능 자동화(Part 1)가 미니 부하가 되지 않도록, 부하 검증(Part 2)과 실행 경로를 분리합니다. 기본 `pytest`는 E2E/API/보안만 돌리고 `tests/loadtest`는 포함하지 않습니다.

| 질문 | Part 1 (기능 CI) | Part 2 (경량 부하, CI 밖) |
| --- | --- | --- |
| 동시성 통제 | 워커 1개, `-n` 없음, 요청 순차 | 5 → 10 → 20 → 30 단계 증설만. `max_workers`는 해당 인원 수 |
| 호출 빈도 상한 | 직렬 실행 + 브라우저 대기. RPS 토큰 버킷은 없음 | 안전성 시나리오에서 3~5초 `sleep`. 요청 timeout 5초 |
| 5xx 재시도 | `APIClient` 재시도 없음. pytest 실패 재실행 플러그인 없음 | HTTP 500 또는 Latency 5초 초과 시 Kill Switch로 즉시 중단 |
| 실행 시점 | Git push CI. 부하 잡과 분리 | 팀 1명만 실행, 지정 시간·피크 제외. 운영 JMeter 금지 |

### 동시성 통제

기능 테스트는 단일 프로세스·단일 워커로만 돌립니다. Jenkins 같은 잡은 동시 빌드를 켜지 않습니다.

부하 테스트만 `ThreadPoolExecutor`로 가상 유저를 엽니다. 한 번에 30명을 넣지 않고 5·10·20·30 순으로 올립니다.

로컬에서도 `-n`과 CI 병렬 매트릭스를 쓰지 않습니다. 팀원 N명이 각자 M 워커로 실행하면 서버에는 N×M 세션이 생깁니다.

### 호출 빈도 상한

Part 1에는 초당 N건 하드캡 코드가 없습니다. 상한은 직렬 실행, Playwright 대기, 부하 스위트 분리로 만듭니다.

Part 2 안전성 통제(`load_safety`)는 스텝 사이에 `random.uniform(3.0, 5.0)`초를 두어 실사용자 클릭 간격을 모사합니다. 부하 클라이언트의 기본 timeout은 5초입니다.

보안 테스트의 반복 로그인 실패(브루트포스)는 단일 스레드·제한 횟수의 기능 검증이며, 부하 파이프라인에 넣지 않습니다.

### 재시도 정책

`APIClient`는 한 번의 `session.request`만 수행합니다. 5xx를 받아 같은 URL을 즉시 다시 치지 않습니다.

`SafetySession`은 응답 코드 500 또는 Latency 5초 초과 시 `SafetyKillSwitchError`를 올려 해당 부하 실행을 끊습니다.

`auto_data`의 짧은 대기·재조회는 생성한 일정이 목록에 보일 때까지의 데이터 준비이며, 5xx 폭풍 재시도가 아닙니다.

### 실행 시점

기능 CI는 코드 푸시 시 돌아갑니다. 부하 테스트는 기본 Jenkins pytest에 넣지 않습니다.

Part 2는 사전 합의된 업무시간에, 팀당 실행 담당 1명만 돌립니다. Loop는 최대 3회, 총 시험 시간은 가이드 하드 리밋(10분)을 넘기지 않습니다. 대상은 Dev sandbox API입니다.

코드가 피크 타임을 시계로 막지는 않습니다. 피크 제외와 1인 실행은 팀 운영 규칙으로 지킵니다.

## E2E/UI/UX Marker

| Marker | E2E/UI/UX TC ID | 테스트 흐름 |
| --- | --- | --- |
| `exam_flow` | ID 1~15 | 시험 응시 및 제출 |
| `board_flow` | ID 16~20 | 게시판 기본 흐름 |
| `schedule_flow` | ID 21~23 | 수업 일정 조회 |
| `exam_retake_flow` | ID 24~26 | 시험 재응시 |
| `schedule_management_flow` | ID 27~35 | 수업 일정 관리 |
| `exam_status_flow` | ID 36~40 | 시험 응시 현황 |
| `exam_multi` | ID 41 | 다중 탭 시험 |
| `exam_reload_save` | ID 42 | 새로고침 후 답안 저장 |
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
pytest -m exam_reload_save -v --headed --slowmo 500
```

## 영상 녹화

| 목적 | 명령어 |
| --- | --- |
| 전체 테스트 녹화 | `--video=on` |
| 실패한 흐름만 보존 | `--video=retain-on-failure` |

영상은 `videos/<테스트 파일명>/` 아래에 저장됩니다.  
`retain-on-failure`는 한 흐름 안에서 테스트 하나라도 실패하면 해당 흐름 전체 영상을 보존합니다.

## Allure 리포트

```powershell
pytest -v --alluredir allure-results --clean-alluredir
allure serve allure-results
```

첫 번째 명령어로 결과를 생성하고, 두 번째 명령어로 로컬 리포트를 엽니다.

## 설치 및 실행

### 1. 가상환경
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 패키지
```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### 3. .env 환경변수
로컬에서는 프로젝트 루트 `.env`를 pytest가 읽습니다. (`.env.sample` 참고)

Jenkins Pipeline은 Secret file Credentials(`seethrough-env`)를 환경 변수로 주입한 뒤 `SEETHROUGH_USE_CREDENTIALS=1`로 `.env` 파일 로드를 건너뜁니다.

## LOAD TEST pytest 실행 방법

부하 테스트는 E2E와 분리되어 있으므로 `pytest` 전체 실행에 포함되지 않습니다.
프로젝트 루트에서 아래 명령어를 사용합니다.

```powershell
pytest tests/loadtest -v -s
pytest tests/loadtest -m load_login -v -s
pytest tests/loadtest -m load_token -v -s
pytest tests/loadtest -m load_transaction -v -s
pytest tests/loadtest -m load_profile -v -s
pytest tests/loadtest -m load_safety -v -s
```

| Marker | TC ID | 테스트 흐름 |
| --- | --- | --- |
| `load_login` | ID 1 | 동시 로그인 |
| `load_token` | ID 2 | 토큰 연동 과목 조회 |
| `load_transaction` | ID 3~7 | 시험 입장·제출·재응시 트랜잭션 |
| `load_profile` | ID 8~11 | 3회 루프 부하 프로필 |
| `load_safety` | ID 12~15 | Kill Switch·Timer 안전성 통제 |

### Allure 결과 누적 생성

`--clean-alluredir`는 사용하지 않습니다. 이전 `allure-report/history`를 다음 실행에 이어 붙여 TREND 그래프가 쌓입니다.

```powershell
pytest tests/loadtest -v -s --alluredir allure-results
allure generate allure-results -o allure-report --clean
allure open allure-report
```
