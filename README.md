# seethrough

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [팀 구성 및 업무 분장](#2-팀-구성-및-업무-분장)
3. [기술 스택](#3-기술-스택)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [코드 작성 기준](#5-코드-작성-기준)
6. [실행 환경 및 설치](#6-실행-환경-및-설치)
7. [테스트 실행 방법](#7-테스트-실행-방법)
8. [핵심 코드 스니펫](#8-핵심-코드-스니펫)
9. [CI/CD 파이프라인](#9-cicd-파이프라인)
10. [테스트 결과 및 산출물](#10-테스트-결과-및-산출물)
11. [Safety Design](#11-safety-design)
12. [트러블슈팅 및 알려진 이슈](#12-트러블슈팅-및-알려진-이슈)
13. [참고 자료](#13-참고-자료)

---

## 1. 프로젝트 소개

### 프로젝트 목적
```
Elice LXP의 핵심 기능을 자동화 테스트로 검증하고 CI를 통해 지속적인 품질 관리를 수행한다.
```

### 테스트 대상 서비스

| 구분 | URL |
| --- | --- |
| Elice LXP(Dev)| [https://dev-qatrack-web.dev.elicer.io/lxp](https://dev-qatrack-web.dev.elicer.io/lxp) |

### 테스트 범위

Elice LXP(Dev)를 대상으로 기능, 보안, 성능 및 사용자 흐름을 검증한다. 테스트 케이스 문서에 설계된 범위는 총 191건이다.

| 테스트 영역 | TC 수 | 주요 검증 범위 |
| --- | ---: | --- |
| [API](https://docs.google.com/spreadsheets/d/19UYRMJlXTdcG8zDIy5Gt8rRAlB0yT8is74YtEo1CMWM/edit?gid=1167603962#gid=1167603962) | 68 | 클래스 홈, 학습 과목, 수업 일정, 게시판 API의 조회·생성·수정·삭제와 학습자·교육자 권한 검증 |
| [API 호출 보안](https://docs.google.com/spreadsheets/d/19UYRMJlXTdcG8zDIy5Gt8rRAlB0yT8is74YtEo1CMWM/edit?gid=1399124983#gid=1399124983) | 47 | 인증 강도, 토큰·세션, BOLA, 권한 상승, 기관·클래스 접근 통제, 비즈니스 로직, 인젝션 및 정보 노출 검증 |
| [부하 테스트](https://docs.google.com/spreadsheets/d/19UYRMJlXTdcG8zDIy5Gt8rRAlB0yT8is74YtEo1CMWM/edit?gid=151845502#gid=151845502) | 16 | 계정·토큰 준비, 과목 조회와 시험 입장·제출·재응시 흐름, 5~30명 부하 프로필, Kill Switch와 호출 간격 검증 |
| [E2E/UI/UX](https://docs.google.com/spreadsheets/d/19UYRMJlXTdcG8zDIy5Gt8rRAlB0yT8is74YtEo1CMWM/edit?gid=1802487519#gid=1802487519) | 60 | 로그인, 클래스·과목·시험, 게시판, 수업 일정, 반응형 UI와 네트워크·중복 요청·시간 초과·HTTP 오류 등 예외 흐름 검증 |

---

## 2. 팀 구성 및 업무 분장

| 팀원 | 역할 | 담당 테스트 영역 | 담당 산출물 |
| --- | --- | --- | --- |
| 이효민 | 팀장 | 부하 테스트 | |
| 박성빈 | 팀원 | API 테스트 | |
| 유대원 | 팀원 | API 테스트 | |
| 홍성우 | 팀원 | E2E/UI/UX 테스트 | QA 자동화 테스트 결과 보고서, README.md |

---

## 3. 기술 스택

### 테스트 도구

| 구분 | 도구 | 용도 |
| --- | --- | --- |
| 테스트 실행 | pytest | 테스트 수집, fixture 및 실행 결과 관리 |
| UI 자동화 | Playwright | Chromium 기반 E2E/UI/UX 테스트 |
| API 테스트 | Requests | HTTP 요청 및 응답 검증 |
| 부하 테스트 |  |  |

### 언어 및 라이브러리

| 구분 | 기술 |
| --- | --- |
| 언어 | Python |
| 테스트 프레임워크 | pytest 9.1.1 |
| 브라우저 자동화 | Playwright 1.62.0, pytest-playwright 0.9.0 |
| HTTP 클라이언트 | Requests 2.34.2 |
| 테스트 리포트 연동 | allure-pytest 2.16.0 |
| 환경변수 로드 | python-dotenv 1.2.3 |

### CI/CD 및 리포트 도구

| 구분 | 도구 | 용도 |
| --- | --- | --- |
| 형상 관리 | GitLab | 소스 코드와 Merge Request 관리 |
| CI | Jenkins | checkout, 환경 구성, 테스트 실행 |
| 실행 환경 | Linux, Docker | Jenkins CI 실행 환경 |
| 리포트 | Allure Report | 테스트 결과와 실패 증거 시각화 |
| 알림 | Discord | Jenkins 빌드 결과 알림 |

---

## 4. 프로젝트 구조

### 주요 폴더

| 경로 | 역할 |
| --- | --- |
| `tests/api/` | 클래스, 과목, 일정, 게시판 API 테스트 |
| `tests/api_security/` | 인증, 권한, 세션 및 웹 보안 테스트 |
| `tests/e2euiux/` | Playwright 기반 E2E/UI/UX 테스트 |
| `tests/loadtest/` | 경량 부하 및 안전성 통제 테스트 |
| `framework/api/` | API 영역별 요청 클라이언트 |
| `framework/api_security/` | API Security 요청 객체, 토큰 및 명세 비교 기능 |
| `framework/e2euiux/` | E2E 공통 flow와 페이지 객체(POM) |
| `framework/loadtest/` | 부하 테스트 클라이언트, pacing, 리포트 및 Kill Switch |
| `clients/` | API와 API Security가 함께 사용하는 기본 HTTP 클라이언트 |
| `config/` | 환경변수 로드와 공통 설정 |
| `data/` | API 명세, 요청 payload와 테스트 데이터 |
| `utils/` | API 계열 assertion, Allure, 데이터 준비 및 공통 유틸리티 |
| `scripts/` | HAR 요약 생성 등 테스트 지원 스크립트 |


### 주요 설정 파일

| 파일 | 역할 |
| --- | --- |
| `.env.sample` | 테스트 실행에 필요한 환경변수 예시 |
| `pytest.ini` | pytest 옵션과 marker 등록 |
| `requirements.txt` | Python 패키지 의존성 |
| `Jenkinsfile` | Jenkins CI 파이프라인 정의 |
| `AGENTS.md` | 프로젝트 작업 범위와 코드 작성 규칙 |

### 테스트 영역별 구성

| 테스트 영역 | 테스트 경로 | Framework/Client | 구성 |
| --- | --- | --- | --- |
| E2E/UI/UX | `tests/e2euiux/` | `framework/e2euiux/` | 사용자 흐름, 예외 상황, 반응형 UI 검증 |
| API | `tests/api/` | `framework/api/`, `clients/` | 클래스, 과목, 일정, 게시판 API 검증 |
| API Security | `tests/api_security/` | `framework/api_security/`, `clients/` | 인증, 세션, BOLA, 권한상승, 인젝션 검증 |
| Load | `tests/loadtest/` | `framework/loadtest/` | 단계별 동시 사용자와 안전성 통제 검증 |

---

## 5. 코드 작성 기준

### 영역별 코드 구조

| 테스트 영역 | 주요 위치 | 구성 기준 |
| --- | --- | --- |
| API | `framework/api/`, `clients/`, `utils/` | 영역별 요청 클라이언트와 공통 HTTP 요청·응답 검증 기능 분리 |
| API Security | `framework/api_security/`, `clients/`, `utils/` | 보안 대상별 요청 객체와 토큰·명세 분석 및 공통 응답 검증 기능 분리 |
| E2E/UI/UX | `framework/e2euiux/pages/`, `framework/e2euiux/flows.py` | 페이지 내부 동작은 POM, 여러 페이지를 잇는 반복 절차는 flow로 관리 |
| Load | `framework/loadtest/` | 계정, 요청 클라이언트, pacing, 안전성 통제와 리포트 기능 분리 |

### E2E POM 기준

| 구분 | 위치 | 기준 |
| --- | --- | --- |
| Page Object | `framework/e2euiux/pages/` | 페이지별 locator, 동작과 화면 검증 관리 |
| Flow | `framework/e2euiux/flows.py` | 여러 페이지에서 반복되는 공통 절차 관리 |

### fixture 사용 기준

| 테스트 영역 | 주요 fixture | 사용 기준 |
| --- | --- | --- |
| 공통 | 각 영역의 `conftest.py` | 반복되는 사전조건과 자원 생명주기를 관리하고 테스트 함수에는 검증 흐름만 유지 |
| API | 사용자별 client, `payloads`, 자동 데이터 탐색 | 여러 TC에서 재사용하는 인증 client와 payload는 `session` scope로 관리 |
| API Security | 사용자별 token과 client | 토큰·세션 간 상태 간섭을 줄이기 위해 기본적으로 함수 단위로 준비 |
| E2E/UI/UX | 계정, 브라우저 context, 시험 초기화 | 계정은 `session`, 연속 flow는 `module`, 독립 상태와 초기화는 `function` scope로 관리 |
| Load | `accounts` | 전체 부하 시나리오에서 사용할 계정 목록을 `session` scope로 한 번 로드 |
| 종료 처리 | 생성 데이터, 브라우저 context와 외부 자원 | fixture에서 생성한 자원은 가능한 경우 `yield` 이후 정리하고 테스트 간 영향을 최소화 |


### marker 및 Allure 메타데이터

| 구분 | 적용 기준 |
| --- | --- |
| pytest marker | 테스트 영역과 flow를 선택 실행하는 기준 |
| `tc_id` | Google Sheet TC와 자동화 결과 연결 |
| `priority` | `P0`, `P1`, `P2` 중요도 구분 |
| `owner` | 테스트 담당자 표시 |
| `team` | 담당 팀 표시 |
| Allure title/feature | API Security 테스트의 기능과 목적 표시 |

marker 목록은 `pytest.ini`, E2E 메타데이터와 수집 순서는 `tests/e2euiux/conftest.py`에서 관리합니다.

### 테스트 실행 순서

| 영역 | 실행 순서 기준 |
| --- | --- |
| E2E/UI/UX | `E2E_FLOW_ORDER`의 flow 순서와 Allure `tc_id` 오름차순 |
| API | 테스트 파일과 함수 수집 순서 |
| API Security | 보안 카테고리별 테스트 파일 수집 순서 |
| Load | marker와 단계별 가상 사용자 수 기준 |

E2E flow는 이전 TC의 화면 상태를 이어받을 수 있으므로 개별 ID만 단독으로 실행하지 않으며, 병렬 실행 옵션을 사용하지 않습니다.

---

## 6. 실행 환경 및 설치

### 지원 환경

| 구분 | 운영체제 | 실행 환경 | 브라우저 |
| --- | --- | --- | --- |
| 로컬 | Windows 11 | Python 가상환경 | Playwright Chromium |
| CI | Linux | Docker 기반 Jenkins | Playwright Chromium |

### 가상환경
```
-
```

### 패키지 설치

```bash
python -m pip install -r requirements.txt
```

### Playwright 브라우저 설치

```bash
python -m playwright install chromium
```

### 환경변수 설정

`.env.sample`을 참고해 프로젝트 루트에 `.env`를 준비합니다. 실제 계정, 비밀번호와 토큰은 저장소에 커밋하지 않습니다.

```powershell
Copy-Item .env.sample .env
```

CI의 민감정보는 `Jenkins Credentials`를 통해 주입하는 방식입니다.

---

## 7. 테스트 실행 방법

### 전체 실행

```bash
pytest
```

기본 `pytest` 실행에는 E2E/UI/UX, API, API Security가 포함되며 부하 테스트는 포함되지 않습니다.

### 영역별 실행

| 영역 | 명령어 |
| --- | --- |
| E2E/UI/UX | `pytest tests/e2euiux -v` |
| API | `pytest tests/api -v` |
| API Security | `pytest tests/api_security -v` |
| Load | `pytest tests/loadtest -v -s` |

### marker 실행

```bash
pytest -m exam_flow -v
pytest -m board -v
pytest -m sec_auth_login -v
pytest tests/loadtest -m load_safety -v -s
```

사용 가능한 marker는 `pytest.ini`에서 확인합니다.

### 영상 녹화

| 옵션 | 설명 |
| --- | --- |
| `--video=on` | 모든 Playwright 테스트 영상 저장 |
| `--video=retain-on-failure` | 실패한 E2E flow 영상만 보존 |

영상은 `videos/<테스트 모듈명>/`에 저장되며 실패 결과는 Allure에 첨부됩니다.

### Allure 리포트 생성

```bash
pytest -v --alluredir allure-results --clean-alluredir
allure serve allure-results
```

### 주요 옵션

| 옵션 | 설명 |
| --- | --- |
| `-v` | 테스트 이름과 결과를 자세히 표시 |
| `--headed` | Playwright 브라우저 화면 표시 |
| `--slowmo 500` | Playwright 동작 사이에 500ms 지연 적용 |
| `--video=retain-on-failure` | 실패한 E2E flow 영상 보존 |
| `--alluredir allure-results` | Allure 원본 결과 저장 경로 지정 |
| `--clean-alluredir` | 실행 전 기존 Allure 원본 결과 삭제 |

통합 실행 예시:

```bash
pytest -v --alluredir allure-results --clean-alluredir --video=retain-on-failure --headed --slowmo 500
```

---

## 8. 핵심 코드 스니펫

### API

클래스 조회 API의 HTTP 성공 여부와 주요 응답 필드를 검증합니다.

```python
def test_api_01(student_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID)
    data = assert_success(
        ClassroomClient(student_client).get_classroom(
            settings.CLASSROOM_ID
        )
    )
    assert str(data.get("id")) == str(settings.CLASSROOM_ID)
    assert data.get("name") not in (None, "")
    assert "description" in data
```

### API Security

로그인 성공 시 HTTP 200과 access token 발급 여부를 검증합니다.

```python
@allure.title("ID-1 정상 로그인 시 토큰 정상 발급")
def test_id01_정상_로그인_토큰_발급(self, account_client):
    response = account_client.login(STUDENT_ID, STUDENT_PW)
    body = json_body(response)

    assert response.status_code == 200
    assert body.get("access_token")
```

### E2E/UI/UX

Allure Label과 POM을 이용해 게시물 작성 흐름을 검증합니다.

```python
@allure.label("tc_id", "46")
@allure.label("priority", "P2")
def test_limit_board_title(board_title_page):
    """게시물 제목 최대 길이 확인"""
    board_write_page = BoardWritePage(board_title_page)
    board_write_page.fill_title(TITLE_VALUE)
    board_write_page.append_title("test")
    board_write_page.verify_title_limit(TITLE_VALUE)
```

### Load

HTTP 500을 감지하면 Kill Switch로 부하 실행을 중단합니다. 가상 유저 기동은 Ramp-up 1초, API·단계 사이는 3~5초 think time을 사용합니다.

```python
from framework.loadtest.pacing import ramp_up_wait, think_time

ramp_up_wait(user_index, user_count)
client = LoadClient(session=SafetySession(session))

try:
    login_response = client.auth.login(login_id, password)
    think_time()
    course_response = client.course.get_course()
except SafetyKillSwitchError as error:
    return False, str(error)
```

---

## 9. CI/CD 파이프라인

### 전체 실행 순서
```
-
```

### GitLab 자동 빌드 조건
```
-
```

### Jenkins Credentials
```
-
```

### Allure 및 Discord 연동
```
-
```

---

## 10. 테스트 결과 및 산출물

| 항목 | 결과 및 이미지 |
| --- | --- |
| TC 문서 | <img src="docs/images/TC_img_01.png" alt="테스트 케이스 문서" width="900"> |
| Allure 리포트 | <img src="docs/images/allure_report_overview.png" alt="Allure 리포트 전체 결과" width="900"><br><br><img src="docs/images/allure_test_detail.png" alt="Allure 테스트 상세 결과" width="900"> |
| Jenkins 실행 결과 | <img src="docs/images/jenkins_pipeline_result.png" alt="Jenkins 파이프라인 실행 결과" width="900"> |
| 결함 및 영상 증거 | ![E2E/UI/UX 45 게시글 중복 작성 결함 영상](docs/bug_videos/e2euiux_45.webm) |

---

## 11. Safety Design

| 안전 항목 | 적용 기준 |
| --- | --- |
| 테스트 대상 환경 제한 | Dev 환경만 사용하며 운영 서비스와 타 과목은 테스트하지 않음 |
| 동시성 및 호출 빈도 제한 | 기능 테스트는 단일 워커로 순차 실행하고, 부하 테스트는 5 → 10 → 20 → 30명 순서로 단계적 증가. 가상 유저는 Ramp-up 1초로 기동을 분산하고, API 사이 및 단계 사이에 3~5초 think time을 둔다 |
| 부하 테스트 분리 | 기본 `pytest`에서 `tests/loadtest`를 제외하고 별도 명령과 담당자를 통해 실행 |
| 재시도 및 Kill Switch | API 5xx를 무조건 재시도하지 않으며, 부하 테스트에서 HTTP 500 감지 시 즉시 중단 |
| 자격증명 보호 | `.env`를 Git에서 제외하고 실패 로그의 계정 정보를 마스킹함. CI 자격증명은 Jenkins Credentials 적용 |
| 테스트 데이터 정리 | 자동 생성 데이터는 세션 종료 시 정리하고, 변경·삭제 테스트는 `destructive` marker로 구분 |


---

## 12. 트러블슈팅 및 알려진 이슈
12-1. 
```
-
```

---

## 13. 참고 자료

| 구분 | 참고 문서 | 활용 내용 |
| --- | --- | --- |
| 테스트 프레임워크 | [pytest 공식 문서](https://docs.pytest.org/en/stable/) | 테스트 실행, fixture, marker 및 pytest hook |
| E2E/UI 자동화 | [Playwright Python 공식 문서](https://playwright.dev/python/docs/intro) | 브라우저 제어, locator, assertion 및 테스트 실행 |
| API 테스트 | [Requests 공식 문서](https://docs.python-requests.org/en/stable/) | HTTP 요청, 인증, 세션 및 응답 처리 |
| API 보안 설계 | [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | 인증, 객체 권한, 자원 소비, 비즈니스 흐름 및 보안 설정 위험 기반 테스트 설계 |
| 부하 테스트 | |  |
| 테스트 리포트 | [Allure Report 공식 문서](https://allurereport.org/docs/) | pytest 결과 수집, 첨부 파일 및 HTML 리포트 생성 |
| CI 파이프라인 | [Jenkins Pipeline 공식 문서](https://www.jenkins.io/doc/book/pipeline/) | Jenkinsfile 기반 테스트 실행과 결과 게시 |
| 자동 빌드 트리거 | [GitLab Webhooks 공식 문서](https://docs.gitlab.com/user/project/integrations/webhooks/) | Push Event와 Jenkins Webhook 연동 |
| 실행 환경 | [Docker 공식 문서](https://docs.docker.com/get-started/) | Jenkins와 테스트 실행 환경의 컨테이너 구성 |
