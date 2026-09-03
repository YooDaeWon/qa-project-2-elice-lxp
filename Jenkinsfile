pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitLab...'
                checkout scm
            }
        }

        stage('Environment Setup') {
            steps {
                echo 'Setting up isolated Python virtual environment and Playwright browsers...'
                sh '''
                    # 매 빌드마다 깨끗한 격리 환경을 위해 기존 venv 폴더 삭제 후 재생성
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                    # Playwright 브라우저 바이너리 설치 (Chromium)
                    python -m playwright install chromium
                '''
            }
        }

        stage('Test Execution') {
            steps {
                echo 'Running pytest in clean environment...'
                sh '''
                    . venv/bin/activate
                    mkdir -p allure-results
                    pytest --alluredir=allure-results --clean-alluredir -v || true
                '''
            }
            post {
                always {
                    // 테스트 완료 후 Allure 결과물을 Jenkins 대시보드에 리포트로 시각화
                    allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                }
            }
        }
    }
}