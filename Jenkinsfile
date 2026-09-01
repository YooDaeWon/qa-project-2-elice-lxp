pipeline {
    agent any

    stages {
        // Stage 1. Checkout (GitLab 소스코드 동기화)
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitLab...'
                checkout scm
            }
        }

        // Stage 2. Environment Setup (Python 가상환경 및 requirements.txt 설치)
        stage('Environment Setup') {
            steps {
                echo 'Setting up Python environment and installing dependencies...'
                // Jenkins 서버 환경이 Windows인 경우 (bat 사용)
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // Stage 3. Test Execution (pytest 실행 및 리포트 아카이빙)
        stage('Test Execution') {
            steps {
                echo 'Running pytest...'
                bat '''
                    call venv\\Scripts\\activate
                    pytest --junitxml=report.xml
                '''
            }
            post {
                always {
                    // 테스트 결과 XML 리포트 아카이빙
                    junit 'report.xml'
                }
            }
        }
    }
    
    // 빌드 성공/실패 시 디스코드 웹훅 알림 전송
    post {
        success {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'SUCCESS',
                description: "빌드가 성공했습니다! 🚀\n프로젝트: ${env.JOB_NAME} (#${env.BUILD_NUMBER})"
            )
        }
        failure {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'FAILURE',
                description: "빌드가 실패했습니다! ❌\n확인이 필요합니다.\n프로젝트: ${env.JOB_NAME} (#${env.BUILD_NUMBER})"
            )
        }
    }
}