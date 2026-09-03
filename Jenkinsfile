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
                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
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
        }
    }
    
    post {
        always {
            // Allure 결과물을 아티팩트로 보존하여 다운로드 및 수동 확인 가능하게 설정
            archiveArtifacts artifacts: 'allure-results/**/*', allowEmptyArchive: true
        }
    }
}