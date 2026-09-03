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
            // 1. Jenkins 대시보드에 Allure 리포트 렌더링 (Allure Jenkins Plugin 필요)
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
        success {
            // 2. 빌드 성공 시 Discord 알림 (Discord Notifier 플러그인 필요시 사용)
            discordSend webhookURL: "https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht", result: 'SUCCESS', description: "빌드가 성공적으로 완료되었습니다."
            echo 'Build Successful!'
        }
        failure {
            // 3. 빌드 실패 시 Discord 알림
            discordSend webhookURL: "https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht", result: 'FAILURE', description: "빌드가 실패했습니다."
            echo 'Build Failed!'
        }
    }
}