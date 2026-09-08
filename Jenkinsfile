pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        ACCOUNT_API_BASE_URL = 'https://dev-qatrack-account-api.dev.elicer.io'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitLab...'
                checkout scm
                // Credentials만 사용. 워크스페이스에 남은 .env는 UI 노출 위험이 있어 제거한다.
                sh 'rm -f .env && echo "workspace .env removed (if present)"'
            }
        }

        stage('Environment Setup') {
            steps {
                echo 'Setting up isolated Python virtual environment and Playwright browsers...'
                sh '''
                    rm -rf venv
                    rm -f .env
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                    python -m playwright install chromium

                    # Jenkins Allure 플러그인(Allure 3)은 에이전트 PATH의 allure CLI를 사용한다.
                    # Docker Jenkins에 npm이 없어도 portable Node로 Allure 3.15.0을 워크스페이스에 설치한다.
                    rm -rf .allure3 .node
                    mkdir -p .allure3 .node
                    NODE_VERSION=v20.19.0
                    NODE_DIST="node-${NODE_VERSION}-linux-x64"
                    if ! command -v npm >/dev/null 2>&1; then
                        echo "npm 없음 → portable Node.js ${NODE_VERSION} 다운로드"
                        curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/${NODE_DIST}.tar.xz" -o .node/node.tar.xz
                        tar -xJf .node/node.tar.xz -C .node
                        export PATH="$PWD/.node/${NODE_DIST}/bin:$PATH"
                    fi
                    npm install --prefix .allure3 allure@3.15.0
                    .allure3/node_modules/.bin/allure --version
                '''
            }
        }

        stage('Test Execution') {
            steps {
                echo 'Running pytest with Jenkins Credentials (no workspace .env read)...'
                withCredentials([file(credentialsId: 'env', variable: 'DOTENV_FILE')]) {
                    sh '''
                        . venv/bin/activate
                        rm -f .env
                        set +x
                        set -a
                        . "$DOTENV_FILE"
                        set +a
                        export SEETHROUGH_USE_CREDENTIALS=1
                        set -x
                        mkdir -p allure-results
                        pytest --video=retain-on-failure --alluredir=allure-results --junitxml=junit-report.xml --clean-alluredir -v || true
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Allure 3 플러그인은 PATH의 allure를 쓴다. portable Node + 워크스페이스 3.15.0을 우선한다.
            withEnv([
                "PATH+ALLURE=${env.WORKSPACE}/.allure3/node_modules/.bin:${env.WORKSPACE}/.node/node-v20.19.0-linux-x64/bin"
            ]) {
                sh '''
                    rm -f .env || true
                    echo "Allure CLI on PATH:"
                    command -v allure || true
                    allure --version || true
                '''
                allure(
                    commandline: 'allure3',
                    includeProperties: false,
                    report: 'allure-report',
                    results: [[path: 'allure-results']]
                )
            }
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
