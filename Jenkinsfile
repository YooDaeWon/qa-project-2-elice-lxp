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
                echo 'Setting up isolated Python virtual environment...'
                sh '''
                    # 매 빌드마다 깨끗한 격리 환경을 위해 기존 venv 폴더 삭제 후 재생성
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
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
        }
    }
}