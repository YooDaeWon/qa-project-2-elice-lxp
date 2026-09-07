# seethrough

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [팀 구성 및 업무 분장](#2-팀-구성-및-업무-분장)
3. [기술 스택](#3-기술-스택)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [테스트 설계](#5-테스트-설계)
6. [코드 작성 기준](#6-코드-작성-기준)
7. [실행 환경 및 설치](#7-실행-환경-및-설치)
8. [테스트 실행 방법](#8-테스트-실행-방법)
9. [핵심 코드 스니펫](#9-핵심-코드-스니펫)
10. [CI/CD 파이프라인](#10-cicd-파이프라인)
11. [테스트 결과 및 산출물](#11-테스트-결과-및-산출물)
12. [Safety Design](#12-safety-design)
13. [트러블슈팅 및 알려진 이슈](#13-트러블슈팅-및-알려진-이슈)
14. [참고 자료](#14-참고-자료)

---

## 1. 프로젝트 소개

### 프로젝트 목적
```
-
```

### 테스트 대상 서비스

| 구분 | URL |
| --- | --- |
| Elice LXP(Dev)| [https://dev-qatrack-web.dev.elicer.io/lxp](https://dev-qatrack-web.dev.elicer.io/lxp) |

### 테스트 범위
```
-
```

---

## 2. 팀 구성 및 업무 분장

| 팀원 | 역할 | 담당 테스트 영역 | 담당 산출물 |
| --- | --- | --- | --- |
| 이효민 | 팀장 | 부하 테스트 | |
| 박성빈 | 팀원 | API 테스트 | |
| 유대원 | 팀원 | API 테스트 | |
| 홍성우 | 팀원 | E2E/UI/UX 테스트 | |

---

## 3. 기술 스택

### 테스트 도구

| 구분 | 도구 | 용도 |
| --- | --- | --- |
| 테스트 실행 | pytest | 테스트 수집, fixture 및 실행 결과 관리 |
| UI 자동화 | Playwright | Chromium 기반 E2E/UI/UX 테스트 |
| API 테스트 | Requests | HTTP 요청 및 응답 검증 |
| 부하 테스트 | ThreadPoolExecutor | 가상 사용자 동시 요청 실행 |

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
| `tests/e2euiux/` | Playwright E2E/UI/UX 테스트 |
| `tests/api/` | 클래스, 과목, 일정, 게시판 API 테스트 |
| `tests/api_security/` | 인증, 권한, 세션 및 웹 보안 테스트 |
| `tests/loadtest/` | 경량 부하 및 안전성 통제 테스트 |
| `framework/e2euiux/` | E2E 공통 flow와 페이지 객체 |
| `framework/api_security/` | API Security 요청 객체와 보안 유틸리티 |
| `framework/loadtest/` | 부하 테스트 클라이언트와 Kill Switch |
| `clients/` | 공통 API 요청 클라이언트 |
| `config/` | 환경변수와 공통 설정 |
| `data/` | API 명세, payload와 테스트 데이터 |
| `utils/` | assertion, Allure, 자동 데이터 준비 유틸리티 |
| `scripts/` | 테스트 지원 스크립트 |
| `videos/` | Playwright 실행 영상 보관 |
| `allure-results/` | Allure 원본 결과 저장 |

### 테스트 영역별 구성

| 테스트 영역 | 테스트 경로 | Framework/Client | 구성 |
| --- | --- | --- | --- |
| E2E/UI/UX | `tests/e2euiux/` | `framework/e2euiux/` | 사용자 흐름, 예외 상황, 반응형 UI 검증 |
| API | `tests/api/` | `clients/` | 클래스, 과목, 일정, 게시판 API 검증 |
| API Security | `tests/api_security/` | `framework/api_security/` | 인증, 세션, BOLA, 권한상승, 인젝션 검증 |
| Load | `tests/loadtest/` | `framework/loadtest/` | 단계별 동시 사용자와 안전성 통제 검증 |

---

## 5. 테스트 설계
```
-
```

---

## 6. 코드 작성 기준

### POM 구조

| 구분 | 위치 | 기준 |
| --- | --- | --- |
| Locator | `framework/e2euiux/pages/` | 페이지별 요소 선택자를 한곳에서 관리 |
| 동작 | `framework/e2euiux/pages/` | 클릭, 입력 등 한 페이지 안의 동작 관리 |
| 검증 | `framework/e2euiux/pages/` | Playwright `expect`를 이용한 화면 상태 검증 |
| Flow | `framework/e2euiux/flows.py` | 여러 페이지에서 반복되는 이동 절차 관리 |

### fixture 사용 기준

| 기준 | 설명 |
| --- | --- |
| `session` scope | 전체 실행에서 공통으로 사용하는 계정 및 설정 관리 |
| `module` scope | 하나의 E2E flow에서 브라우저 상태 공유 |
| `function` scope | 서로 영향을 주면 안 되는 독립 테스트 상태 관리 |
| 종료 처리 | context, session과 자동 생성 데이터 정리 |
| 사전조건 | 로그인, 시험 재응시 허용, API 테스트 데이터 준비 |

### locator 기준

| 우선순위 | 기준 | 예시 |
| ---: | --- | --- |
| 1 | 입력 요소의 안정적인 `name` 속성 | `locator('input[name="loginId"]')` |
| 2 | 버튼과 링크의 role 및 접근성 이름 | `get_by_role("button", name="로그인")` |
| 3 | 고유한 화면 문구 | `get_by_text("페이지를 찾을 수 없습니다.")` |
| 4 | 안정적인 CSS 속성 | `locator('[data-lexical-editor="true"]')` |


### marker 및 Allure 메타데이터

| 구분 | 적용 기준 |
| --- | --- |
| pytest marker | 테스트 영역과 flow를 선택 실행하는 기준 |
| `tc_id` | Google Sheet TC와 자동화 결과 연결 |
| `priority` | `P1`, `P2` 중요도 구분 |
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

E2E flow는 이전 TC의 화면 상태를 이어받을 수 있으므로 개별 ID만 단독으로 실행하지 않으며, 병렬 실행 옵션 `-n`을 사용하지 않습니다.

---

## 7. 실행 환경 및 설치

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

CI의 민감정보는 Jenkins Credentials를 통해 주입하는 방식입니다.

---

## 8. 테스트 실행 방법

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

## 9. 핵심 코드 스니펫

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
### 3. .env 환경변수
로컬에서는 프로젝트 루트 `.env`를 pytest가 읽습니다. (`.env.sample` 참고)

Jenkins Pipeline은 Secret file Credentials(`seethrough-env`)를 환경 변수로 주입한 뒤 `SEETHROUGH_USE_CREDENTIALS=1`로 `.env` 파일 로드를 건너뜁니다.

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

응답 지연이나 HTTP 500을 감지하면 Kill Switch로 부하 실행을 중단합니다.

```python
client = LoadClient(session=SafetySession(session), timeout=6)

try:
    login_response = client.auth.login(login_id, password)
except SafetyKillSwitchError as error:
    return False, str(error)
```

---

## 10. CI/CD 파이프라인

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

## 11. 테스트 결과 및 산출물

| 항목 | 결과 및 이미지 |
| --- | --- |
| TC 문서 | |
| Allure 리포트 | |
| Jenkins 실행 결과 | |
| 결함 및 영상 증거 | |

---

## 12. Safety Design

| 안전 항목 | 적용 기준 |
| --- | --- |
| 테스트 대상 환경 제한 | Dev 환경만 사용하며 운영 서비스와 타 과목은 테스트하지 않음 |
| 동시성 및 호출 빈도 제한 | 기능 테스트는 단일 워커로 순차 실행하고, 부하 테스트는 5 → 10 → 20 → 30명 순서로 단계적 증가 |
| 부하 테스트 분리 | 기본 `pytest`에서 `tests/loadtest`를 제외하고 별도 명령과 담당자를 통해 실행 |
| 재시도 및 Kill Switch | API 5xx를 무조건 재시도하지 않으며, 부하 테스트에서 HTTP 500 또는 5초 초과 지연 감지 시 즉시 중단 |
| 자격증명 보호 | `.env`를 Git에서 제외하고 실패 로그의 계정 정보를 마스킹함. CI 자격증명은 Jenkins Credentials로 이전 필요 |
| 테스트 데이터 정리 | 자동 생성 데이터는 세션 종료 시 정리하고, 변경·삭제 테스트는 `destructive` marker로 구분 |

E2E/UI/UX 테스트는 테스트 간 상태 충돌을 방지하기 위해 `pytest-xdist` 병렬 실행 옵션 `-n`을 사용하지 않습니다.

---

## 13. 트러블슈팅 및 알려진 이슈
13-1. 
```
-
```

---

## 14. 참고 자료
```
-
```
