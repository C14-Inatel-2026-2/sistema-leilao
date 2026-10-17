pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = 'phpaiva05'
        GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        IMAGE = "${DOCKER_HUB_USER}/sistema-leilao:${GIT_SHA}"
        TEST_CONTAINER = "leilao-test-${GIT_SHA}"
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t "$IMAGE" .'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set +e
                    docker run --name "$TEST_CONTAINER" "$IMAGE"
                    status=$?
                    mkdir -p reports
                    docker cp "$TEST_CONTAINER:/app/reports/." reports/ || true
                    docker rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true
                    exit $status
                '''
            }
        }

        stage('Coverage Report') {
            steps {
                // Le o coverage.xml gerado no stage Test e publica no Jenkins.
                // Os caminhos no XML sao relativos a cada pacote, por isso as
                // pastas de codigo-fonte sao listadas uma a uma.
                recordCoverage(
                    tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']],
                    id: 'coverage',
                    name: 'Cobertura de Testes',
                    sourceDirectories: [
                        [path: 'domain'],
                        [path: 'use_cases'],
                        [path: 'adapters'],
                        [path: 'infra'],
                    ],
                    qualityGates: [
                        [threshold: 70.0, metric: 'LINE', baseline: 'PROJECT', criticality: 'UNSTABLE'],
                    ]
                )
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo "Enviando imagem para o Docker Hub: ${IMAGE}"
                withCredentials([usernamePassword(credentialsId: 'docker-hub', 
                                                 usernameVariable: 'DH_USER', 
                                                 passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE"
                    '''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo 'Pipeline finalizado com sucesso!'
        }
        failure {
            echo 'Falha em alguma das etapas do pipeline.'
        }
    }
}
