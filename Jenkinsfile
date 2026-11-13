// Tags no Docker Hub: <tipo>-<nnnn> (main-0001, main-0002, feature-0001).
// nnnn é o maior sufixo de 4 dígitos daquele prefixo + 1, no lugar do hash.
// Quatro dígitos não colidem com o hash curto antigo (feature-6020901).
// A branch main também move a tag latest, que o Render usa como referência.
pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = 'phpaiva05'
        GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        // Tipo da branch (feature, chore, fix, dev, main...). Em PR usa a branch de origem.
        BRANCH_TYPE = sh(returnStdout: true, script: '''
            branch="${CHANGE_BRANCH:-${BRANCH_NAME:-$(git rev-parse --abbrev-ref HEAD)}}"
            branch="${branch#origin/}"
            branch=$(printf '%s' "$branch" | sed 's#%2[Ff]#/#g')
            case "$branch" in
                */*) type="${branch%%/*}" ;;
                *) type="$branch" ;;
            esac
            type=$(printf '%s' "$type" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9._-' '-')
            type=$(printf '%s' "$type" | sed 's/^-*//;s/-*$//')
            case "$type" in
                ""|head) type=build ;;
            esac
            printf '%s' "$type"
        ''').trim()
        // Nome só local. A tag publicada (main-0012, feature-0003, ...) sai no push.
        LOCAL_IMAGE = "sistema-leilao:ci-${GIT_SHA}"
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
                sh '''
                    docker build \
                        --platform linux/amd64 \
                        --label "org.opencontainers.image.revision=${GIT_SHA}" \
                        -t "$LOCAL_IMAGE" .
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set +e
                    docker run --name "$TEST_CONTAINER" "$LOCAL_IMAGE" \
                        pytest -q --cov --cov-report=term-missing \
                        --cov-report=xml:reports/coverage.xml \
                        --junitxml=reports/junit.xml
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
                                    "$LOCAL_IMAGE" > reports/trivy.txt
                                status=$?
                                cat reports/trivy.txt
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v trivy-cache:/root/.cache \
                                    aquasec/trivy:latest image \
                                    --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 \
                                    --format template --template "@/contrib/junit.tpl" \
                                    "$LOCAL_IMAGE" > reports/trivy-junit.xml || true
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
                                    anchore/grype:latest "docker:$LOCAL_IMAGE" \
                                    --only-fixed --fail-on high > reports/grype.txt
                                status=$?
                                cat reports/grype.txt
                                docker run --rm \
                                    -v /var/run/docker.sock:/var/run/docker.sock \
                                    -v grype-cache:/root/.cache \
                                    anchore/grype:latest "docker:$LOCAL_IMAGE" \
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
                echo "Publicando ${BRANCH_TYPE}-<nnnn> de ${LOCAL_IMAGE}"
                withCredentials([usernamePassword(credentialsId: 'docker-hub',
                                                 usernameVariable: 'DH_USER',
                                                 passwordVariable: 'DH_PASS')]) {
                    sh '''
                        set -euo pipefail
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        tag=$(docker run --rm -i \
                            -e DOCKER_HUB_USER \
                            -e BRANCH_TYPE \
                            --entrypoint python \
                            "$LOCAL_IMAGE" - <<'PY'
import json
import os
import re
import urllib.error
import urllib.request

user = os.environ["DOCKER_HUB_USER"]
prefix = os.environ["BRANCH_TYPE"]
pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{4}})$")
url = (
    "https://hub.docker.com/v2/repositories/"
    f"{user}/sistema-leilao/tags?page_size=100"
)
highest = 0
try:
    while url:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.load(resp)
        for item in data.get("results", []):
            match = pattern.fullmatch(item.get("name") or "")
            if match:
                highest = max(highest, int(match.group(1)))
        url = data.get("next")
except urllib.error.HTTPError as exc:
    if exc.code != 404:
        raise

candidate = highest + 1
while candidate <= 9999:
    name = f"{prefix}-{candidate:04d}"
    check = (
        "https://hub.docker.com/v2/repositories/"
        f"{user}/sistema-leilao/tags/{name}"
    )
    try:
        with urllib.request.urlopen(check, timeout=60) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(name)
            break
        raise
    candidate += 1
else:
    raise SystemExit(f"nenhuma tag livre para o prefixo {prefix}")
PY
                        )
                        tag=$(printf '%s' "$tag" | tr -d '[:space:]')
                        suffix=${tag#"${BRANCH_TYPE}-"}
                        case "$suffix" in
                            [0-9][0-9][0-9][0-9]) ;;
                            *)
                                echo "Tag inesperada: '$tag'" >&2
                                exit 1
                                ;;
                        esac
                        remote="${DOCKER_HUB_USER}/sistema-leilao:${tag}"
                        docker tag "$LOCAL_IMAGE" "$remote"
                        docker push "$remote"
                        printf '%s\n' "docker.io/${remote}" > .image-ref
                        echo "Imagem publicada: docker.io/${remote} (commit ${GIT_SHA})"
                        if [ "${BRANCH_NAME}" = "main" ] && [ -z "${CHANGE_ID:-}" ]; then
                            latest="${DOCKER_HUB_USER}/sistema-leilao:latest"
                            docker tag "$LOCAL_IMAGE" "$latest"
                            docker push "$latest"
                            echo "Tag latest agora aponta para ${tag}"
                        fi
                    '''
                }
            }
        }

        // O Render não redeploya sozinho quando a tag latest se move.
        // Credencial (Secret text): a URL do deploy hook do serviço, em
        // Settings. O hook publica esta build (main-0012), não só latest.
        stage('Deploy on Render') {
            when { branch 'main' }
            steps {
                withCredentials([string(credentialsId: 'render-deploy-hook',
                                       variable: 'RENDER_DEPLOY_HOOK')]) {
                    sh '''
                        set -eu
                        image_ref=$(tr -d '[:space:]' < .image-ref)
                        echo "Disparando deploy no Render de ${image_ref}"
                        docker run --rm -i \
                            --entrypoint python \
                            -e RENDER_DEPLOY_HOOK \
                            -e IMAGE_REF="$image_ref" \
                            "$LOCAL_IMAGE" - <<'PY'
import os
import urllib.parse
import urllib.request

hook = os.environ["RENDER_DEPLOY_HOOK"]
image = os.environ["IMAGE_REF"]
separator = "&" if "?" in hook else "?"
url = hook + separator + "imgURL=" + urllib.parse.quote(image, safe="")
request = urllib.request.Request(url, method="POST")
with urllib.request.urlopen(request, timeout=60) as response:
    print(response.status)
    print(response.read().decode())
PY
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'rm -f .image-ref'
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
