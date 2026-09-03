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
                    # Allure 결과 외에 JUnit XML 리포트도 함께 생성 (통계 파싱용)
                    pytest --alluredir=allure-results --junitxml=junit-report.xml --clean-alluredir -v || true
                '''
            }
        }
    }
    
    post {
        always {
            // 1. Jenkins 대시보드에 Allure 리포트 렌더링
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
        success {
            script {
                def total = 0, failures = 0, errors = 0, skipped = 0, passed = 0
                if (fileExists('junit-report.xml')) {
                    def junitXml = new groovy.xml.XmlSlurper().parse(readFile('junit-report.xml'))
                    total = junitXml.@tests.text() ? junitXml.@tests.text().toInteger() : 0
                    failures = junitXml.@failures.text() ? junitXml.@failures.text().toInteger() : 0
                    errors = junitXml.@errors.text() ? junitXml.@errors.text().toInteger() : 0
                    skipped = junitXml.@skipped.text() ? junitXml.@skipped.text().toInteger() : 0
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
        failure {
            script {
                def total = 0, failures = 0, errors = 0, skipped = 0, passed = 0
                if (fileExists('junit-report.xml')) {
                    def junitXml = new groovy.xml.XmlSlurper().parse(readFile('junit-report.xml'))
                    total = junitXml.@tests.text() ? junitXml.@tests.text().toInteger() : 0
                    failures = junitXml.@failures.text() ? junitXml.@failures.text().toInteger() : 0
                    errors = junitXml.@errors.text() ? junitXml.@errors.text().toInteger() : 0
                    skipped = junitXml.@skipped.text() ? junitXml.@skipped.text().toInteger() : 0
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