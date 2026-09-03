pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
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
                echo 'Setting up Python dependencies...'
                sh '''
                    python -m pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Test Execution') {
            steps {
                echo 'Running pytest...'
                sh '''
                    mkdir -p allure-results
                    pytest --alluredir=allure-results --clean-alluredir -v || true
                '''
            }
        }
    }
}