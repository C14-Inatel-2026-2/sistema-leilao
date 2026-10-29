pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = 'phpaiva05'
        GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        IMAGE = "${DOCKER_HUB_USER}/sistema-leilao:${GIT_SHA}"
        TEST_CONTAINER = "leilao-test-${GIT_SHA}"
        RUFF_IMAGE = 'ghcr.io/astral-sh/ruff:0.17.3-alpine'
    }

    stages {
        stage('Lint Dockerfile (Hadolint)') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                    sh '''
                        mkdir -p reports
                        set +e
                        docker run --rm -i hadolint/hadolint hadolint --failure-threshold warning - < Dockerfile > reports/hadolint.txt
                        status=$?
                        cat reports/hadolint.txt
                        docker run --rm -i hadolint/hadolint hadolint --no-fail -f json - < Dockerfile > reports/hadolint.json || true
                        docker run --rm -i ghcr.io/jqlang/jq:latest -r "$(cat tools/junit/hadolint.jq)" < reports/hadolint.json > reports/hadolint-junit.xml || true
                        exit $status
                    '''
                }
            }
        }

        stage('Lint Python (Ruff)') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                    // O codigo vai por stdin (tar), como o Dockerfile no Hadolint:
                    // montar o workspace (-v) nao funciona com o Jenkins em container.
                    // Verifica lint (ruff check) e formatacao (ruff format --check).
                    sh '''
                        mkdir -p reports
                        set +e
                        tar -cf - pyproject.toml domain use_cases adapters infra tests \
                            | docker run --rm -i --entrypoint sh "$RUFF_IMAGE" -c \
                                'mkdir /src && tar -xf - -C /src && cd /src \
                                 && ruff check --no-cache --output-format concise . 2>&1; lint=$?; \
                                 ruff format --no-cache --check . 2>&1; fmt=$?; \
                                 exit $((lint | fmt))' \
                            > reports/ruff.txt
                        status=$?
                        cat reports/ruff.txt
                        tar -cf - pyproject.toml domain use_cases adapters infra tests \
                            | docker run --rm -i --entrypoint sh "$RUFF_IMAGE" -c \
                                'mkdir /src && tar -xf - -C /src && cd /src && ruff check --no-cache --exit-zero --output-format junit .' \
                            > reports/ruff-junit.xml || true
                        exit $status
                    '''
                }
            }
        }

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

        stage('Security Scan') {
            parallel {
                stage('Trivy') {
                    steps {
                        catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                            sh '''
                                mkdir -p reports
                                set +e
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v trivy-cache:/root/.cache \
                                    aquasec/trivy:latest image \
                                    --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 \
                                    "$IMAGE" > reports/trivy.txt
                                status=$?
                                cat reports/trivy.txt
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v trivy-cache:/root/.cache \
                                    aquasec/trivy:latest image \
                                    --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 \
                                    --format template --template "@/contrib/junit.tpl" \
                                    "$IMAGE" > reports/trivy-junit.xml || true
                                exit $status
                            '''
                        }
                    }
                }
                stage('Grype') {
                    steps {
                        catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                            sh '''
                                mkdir -p reports
                                set +e
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v grype-cache:/root/.cache \
                                    anchore/grype:latest "docker:$IMAGE" \
                                    --only-fixed --fail-on high > reports/grype.txt
                                status=$?
                                cat reports/grype.txt
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v grype-cache:/root/.cache \
                                    anchore/grype:latest "docker:$IMAGE" \
                                    --only-fixed -o json > reports/grype.json || true
                                docker run --rm -i ghcr.io/jqlang/jq:latest -r "$(cat tools/junit/grype.jq)" < reports/grype.json > reports/grype-junit.xml || true
                                exit $status
                            '''
                        }
                    }
                }
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
            junit allowEmptyResults: true, testResults: 'reports/*junit*.xml'
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
