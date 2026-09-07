pipeline {
    agent any

    environment {
        ACCOUNT_API_BASE_URL = 'https://dev-qatrack-account-api.dev.elicer.io'
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
                echo 'Running pytest with Jenkins Credentials (no workspace .env read)...'
                withCredentials([file(credentialsId: 'seethrough-env', variable: 'DOTENV_FILE')]) {
                    sh '''
                        . venv/bin/activate
                        set -a
                        . "$DOTENV_FILE"
                        set +a
                        export SEETHROUGH_USE_CREDENTIALS=1
                        mkdir -p allure-results
                        pytest --video=retain-on-failure --alluredir=allure-results --junitxml=junit-report.xml --clean-alluredir -v || true
                    '''
                }
            }
        }
    }
    
    post {
        always {
            allure allureVersion: '3', includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
        success {
            script {
                def total = 0, failures = 0, errors = 0, skipped = 0, passed = 0
                if (fileExists('junit-report.xml')) {
                    def content = readFile('junit-report.xml')
                    def testsuitesMatcher = content =~ /tests="(\d+)"/
                    if (testsuitesMatcher) total = testsuitesMatcher[0][1].toInteger()
                    def failuresMatcher = content =~ /failures="(\d+)"/
                    if (failuresMatcher) failures = failuresMatcher[0][1].toInteger()
                    def errorsMatcher = content =~ /errors="(\d+)"/
                    if (errorsMatcher) errors = errorsMatcher[0][1].toInteger()
                    def skippedMatcher = content =~ /skipped="(\d+)"/
                    if (skippedMatcher) skipped = skippedMatcher[0][1].toInteger()
                    
                    passed = total - (failures + errors + skipped)
                }
                def passRate = total > 0 ? String.format("%.1f", (passed / total) * 100) : "0.0"
                def message = "• 프로젝트: seethrough-pipeline (qa6_team4)\n• 테스트 결과 요약: Total [${total}] / Pass [${passed}] / Fail [${failures + errors}]\n• 최종 성공률: ${passRate}%\n\n[상세 로그 및 Allure 시각화 대시보드 확인하기](${env.BUILD_URL})"
                
                discordSend webhookURL: "https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht",
                            result: 'SUCCESS',
                            title: "Jenkins Build #${env.BUILD_NUMBER} - SUCCESS",
                            description: message
            }
            echo 'Build Successful!'
        }
        unstable {
            script {
                def total = 0, failures = 0, errors = 0, skipped = 0, passed = 0
                if (fileExists('junit-report.xml')) {
                    def content = readFile('junit-report.xml')
                    def testsuitesMatcher = content =~ /tests="(\d+)"/
                    if (testsuitesMatcher) total = testsuitesMatcher[0][1].toInteger()
                    def failuresMatcher = content =~ /failures="(\d+)"/
                    if (failuresMatcher) failures = failuresMatcher[0][1].toInteger()
                    def errorsMatcher = content =~ /errors="(\d+)"/
                    if (errorsMatcher) errors = errorsMatcher[0][1].toInteger()
                    def skippedMatcher = content =~ /skipped="(\d+)"/
                    if (skippedMatcher) skipped = skippedMatcher[0][1].toInteger()
                    
                    passed = total - (failures + errors + skipped)
                }
                def passRate = total > 0 ? String.format("%.1f", (passed / total) * 100) : "0.0"
                def message = "• 프로젝트: seethrough-pipeline (qa6_team4)\n• 테스트 결과 요약: Total [${total}] / Pass [${passed}] / Fail [${failures + errors}]\n• 최종 성공률: ${passRate}%\n\n[상세 로그 및 Allure 시각화 대시보드 확인하기](${env.BUILD_URL})"
                
                discordSend webhookURL: "https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht",
                            result: 'UNSTABLE',
                            title: "Jenkins Build #${env.BUILD_NUMBER} - UNSTABLE",
                            description: message
            }
            echo 'Build Unstable!'
        }
        failure {
            script {
                def total = 0, failures = 0, errors = 0, skipped = 0, passed = 0
                if (fileExists('junit-report.xml')) {
                    def content = readFile('junit-report.xml')
                    def testsuitesMatcher = content =~ /tests="(\d+)"/
                    if (testsuitesMatcher) total = testsuitesMatcher[0][1].toInteger()
                    def failuresMatcher = content =~ /failures="(\d+)"/
                    if (failuresMatcher) failures = failuresMatcher[0][1].toInteger()
                    def errorsMatcher = content =~ /errors="(\d+)"/
                    if (errorsMatcher) errors = errorsMatcher[0][1].toInteger()
                    def skippedMatcher = content =~ /skipped="(\d+)"/
                    if (skippedMatcher) skipped = skippedMatcher[0][1].toInteger()
                    
                    passed = total - (failures + errors + skipped)
                }
                def passRate = total > 0 ? String.format("%.1f", (passed / total) * 100) : "0.0"
                def message = "• 프로젝트: seethrough-pipeline (qa6_team4)\n• 테스트 결과 요약: Total [${total}] / Pass [${passed}] / Fail [${failures + errors}]\n• 최종 성공률: ${passRate}%\n\n[상세 로그 및 Allure 시각화 대시보드 확인하기](${env.BUILD_URL})"
                
                discordSend webhookURL: "https://discord.com/api/webhooks/1544267640154103849/3_Lr6kUahhWLpqslIk0WBvZ6KtDUhMggMpatqzWUY6SoWCw7OUoT8yBmY_urSu5X-iht",
                            result: 'FAILURE',
                            title: "Jenkins Build #${env.BUILD_NUMBER} - FAILURE",
                            description: message
            }
            echo 'Build Failed!'
        }
    }
}
