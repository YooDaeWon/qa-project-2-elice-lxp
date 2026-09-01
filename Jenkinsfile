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
            script {
                def webhookUrl = 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht'
                def titleMsg = "Jenkins Build #${env.BUILD_NUMBER} - SUCCESS"
                def descMsg = "• 프로젝트: ${env.JOB_NAME}\\n• 빌드 상태: 성공\\n• [상세 로그 및 Jenkins 링크 확인하기](${env.BUILD_URL})"
                
                def jsonPayload = """
                {
                    "embeds": [{
                        "title": "${titleMsg}",
                        "description": "${descMsg}",
                        "color": 3066993
                    }]
                }
                """
                
                writeFile file: 'discord_success.json', text: jsonPayload
                bat 'curl -H "Content-Type: application/json" -X POST -d "@discord_success.json" ' + webhookUrl
            }
        }
        failure {
            script {
                def webhookUrl = 'https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht'
                def titleMsg = "Jenkins Build #${env.BUILD_NUMBER} - FAILURE"
                def descMsg = "• 프로젝트: ${env.JOB_NAME}\\n• 빌드 상태: 실패 (확인 필요)\\n• [상세 로그 및 Jenkins 링크 확인하기](${env.BUILD_URL})"
                
                def jsonPayload = """
                {
                    "embeds": [{
                        "title": "${titleMsg}",
                        "description": "${descMsg}",
                        "color": 15158332
                    }]
                }
                """
                
                writeFile file: 'discord_fail.json', text: jsonPayload
                bat 'curl -H "Content-Type: application/json" -X POST -d "@discord_fail.json" ' + webhookUrl
            }
        }
    }
}