pipeline {
    agent any

    environment {
        IMAGE = "sistema-leilao:${BUILD_NUMBER}"
        TEST_CONTAINER = "leilao-test-${BUILD_NUMBER}"
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
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            sh 'docker rmi "$IMAGE" >/dev/null 2>&1 || true'
        }
        success {
            echo 'Build e testes concluidos com sucesso.'
        }
        failure {
            echo 'Falha no build ou nos testes.'
        }
    }
}
