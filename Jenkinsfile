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
                echo 'Setting up Python environment and installing dependencies...'
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

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
                    junit 'report.xml'
                }
            }
        }
    }
    
    post {
        success {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'SUCCESS',
                message: "빌드가 성공했습니다! 🚀 (프로젝트: ${env.JOB_NAME} #${env.BUILD_NUMBER})"
            )
        }
        failure {
            discordSend(
                webhookURL: 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht',
                result: 'FAILURE',
                message: "빌드가 실패했습니다! ❌ 확인이 필요합니다. (프로젝트: ${env.JOB_NAME} #${env.BUILD_NUMBER})"
            )
        }
    }
}