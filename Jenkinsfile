pipeline {
    agent any

    environment {
        PYTHONUTF8 = '1'
        PYTHONIOENCODING = 'utf-8'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitLab...'
                checkout scm
            }
        }

        stage('Environment Setup') {
            steps {
                echo 'Setting up Python environment and dependencies...'
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m playwright install chromium
                '''
            }
        }

        stage('Test Execution') {
            steps {
                echo 'Running pytest with Allure...'
                bat '''
                    chcp 65001
                    cd /d "%WORKSPACE%"
                    if not exist allure-results mkdir allure-results
                    venv\\Scripts\\python.exe -m pytest tests/e2euiux tests/api --alluredir=allure-results --clean-alluredir -v
                    set PYTEST_EXIT=%ERRORLEVEL%
                    echo ===== allure-results =====
                    dir allure-results
                    exit /b %PYTEST_EXIT%
                '''
            }
            post {
                always {
                    allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                }
            }
        }
    }
    
    post {
        success {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'SUCCESS',
                title: "Jenkins Build #${env.BUILD_NUMBER} - SUCCESS",
                description: "• 프로젝트: ${env.JOB_NAME}\n• 빌드 상태: 성공\n• [상세 로그 및 Jenkins 링크 확인하기](${env.BUILD_URL})"
            )
        }
        failure {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'FAILURE',
                title: "Jenkins Build #${env.BUILD_NUMBER} - FAILURE",
                description: "• 프로젝트: ${env.JOB_NAME}\n• 빌드 상태: 실패 (확인 필요)\n• [상세 로그 및 Jenkins 링크 확인하기](${env.BUILD_URL})"
            )
        }
    }
}