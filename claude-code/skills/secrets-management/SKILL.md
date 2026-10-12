---
# Derived from https://github.com/wshobson/agents/plugins/cicd-automation/skills/secrets-management @ 46891e7 on 2026-10-09 (no secret echo; trufflehog --fail; gitleaks primary) — aa-ma-forge v0.17.0
name: secrets-management
description: Implement secure secrets management for CI/CD pipelines using Vault, AWS Secrets Manager, or native platform solutions. Use when handling sensitive credentials, rotating secrets, or securing CI/CD environments.
---

# Secrets Management

Secure secrets management practices for CI/CD pipelines using Vault, AWS Secrets Manager, and other tools.

## Purpose

Implement secure secrets management in CI/CD pipelines without hardcoding sensitive information.

## When to Use

- Store API keys and credentials
- Manage database passwords
- Handle TLS certificates
- Rotate secrets automatically
- Implement least-privilege access

## Secrets Management Tools

### HashiCorp Vault

- Centralized secrets management
- Dynamic secrets generation
- Secret rotation
- Audit logging
- Fine-grained access control

### AWS Secrets Manager

- AWS-native solution
- Automatic rotation
- Integration with RDS
- CloudFormation support

### Azure Key Vault

- Azure-native solution
- HSM-backed keys
- Certificate management
- RBAC integration

### Google Secret Manager

- GCP-native solution
- Versioning
- IAM integration

## HashiCorp Vault Integration

### Setup Vault

```bash
# Start Vault dev server
vault server -dev

# Set environment
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

# Enable secrets engine
vault secrets enable -path=secret kv-v2

# Store secret
vault kv put secret/database/config username=admin password=secret
```

### GitHub Actions with Vault

```yaml
name: Deploy with Vault Secrets

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Import Secrets from Vault
        uses: hashicorp/vault-action@v2
        with:
          url: https://vault.example.com:8200
          token: ${{ secrets.VAULT_TOKEN }}
          secrets: |
            secret/data/database username | DB_USERNAME ;
            secret/data/database password | DB_PASSWORD ;
            secret/data/api key | API_KEY

      - name: Use secrets
        run: |
          echo "Connecting to database as $DB_USERNAME"
          # Use $DB_PASSWORD, $API_KEY
```

### GitLab CI with Vault

```yaml
deploy:
  image: vault:1.17
  before_script:
    - export VAULT_ADDR=https://vault.example.com:8200
    - export VAULT_TOKEN=$VAULT_TOKEN
    - apk add curl jq
  script:
    - |
      DB_PASSWORD=$(vault kv get -field=password secret/database/config)
      API_KEY=$(vault kv get -field=key secret/api/credentials)
      echo "Deploying with secrets..."
      # Use $DB_PASSWORD, $API_KEY
```

## AWS Secrets Manager

### Store Secret

```bash
aws secretsmanager create-secret \
  --name production/database/password \
  --secret-string "super-secret-password"
```

### Retrieve in GitHub Actions

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-west-2

- name: Get secret from AWS
  run: |
    SECRET=$(aws secretsmanager get-secret-value \
      --secret-id production/database/password \
      --query SecretString \
      --output text)
    echo "::add-mask::$SECRET"
    echo "DB_PASSWORD=$SECRET" >> $GITHUB_ENV

- name: Use secret
  run: |
    # Use $DB_PASSWORD
    ./deploy.sh
```

### Terraform with AWS Secrets Manager

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "production/database/password"
}

resource "aws_db_instance" "main" {
  allocated_storage    = 100
  engine              = "postgres"
  instance_class      = "db.t3.large"
  username            = "admin"
  password            = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}
```

## GitHub Secrets

### Organization/Repository Secrets

```yaml
- name: Use GitHub secret
  env:
    API_KEY: ${{ secrets.API_KEY }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    # Secrets are injected as env vars — never print them to logs
    ./deploy.sh
```

### Environment Secrets

```yaml
deploy:
  runs-on: ubuntu-latest
  environment: production
  steps:
    - name: Deploy
      env:
        PROD_API_KEY: ${{ secrets.PROD_API_KEY }}
      run: |
        # Secret injected as env var — never print to logs
        ./deploy.sh
```

## GitLab CI/CD Variables

### Project Variables

```yaml
deploy:
  script:
    # $API_KEY / $DATABASE_URL are injected as env vars — never echo them to the job log
    - ./deploy.sh
```

### Protected and Masked Variables

- Protected: Only available in protected branches
- Masked: Hidden in job logs
- File type: Stored as file

## Best Practices

1. **Never commit secrets** to Git
2. **Use different secrets** per environment
3. **Rotate secrets regularly**
4. **Implement least-privilege access**
5. **Enable audit logging**
6. **Use secret scanning** (gitleaks; TruffleHog as an alternative)
7. **Mask secrets in logs**
8. **Encrypt secrets at rest**
9. **Use short-lived tokens** when possible
10. **Document secret requirements**

## Secret Rotation

### Automated Rotation with AWS

```python
import boto3
import json

def lambda_handler(event, context):
    client = boto3.client('secretsmanager')

    # Get current secret
    response = client.get_secret_value(SecretId='my-secret')
    current_secret = json.loads(response['SecretString'])

    # Generate new password
    new_password = generate_strong_password()

    # Update database password
    update_database_password(new_password)

    # Update secret
    client.put_secret_value(
        SecretId='my-secret',
        SecretString=json.dumps({
            'username': current_secret['username'],
            'password': new_password
        })
    )

    return {'statusCode': 200}
```

### Manual Rotation Process

1. Generate new secret
2. Update secret in secret store
3. Update applications to use new secret
4. Verify functionality
5. Revoke old secret

## External Secrets Operator

### Kubernetes Integration

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.example.com:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "production"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: database/config
        property: username
    - secretKey: password
      remoteRef:
        key: database/config
        property: password
```

## Secret Scanning

gitleaks is the primary scanner: staged changes at commit, full history in CI. Ignore a
reviewed false positive by its fingerprint (`commit:file:rule:line`) in `.gitleaksignore`,
with a `# why:` line above it, never by a path or regex allowlist.

### Pre-commit (staged changes)

```yaml
# .pre-commit-config.yaml — hook definition from a SHA-frozen rev; runs the installed binary
- repo: https://github.com/gitleaks/gitleaks
  rev: <40-hex commit of the release tag>  # frozen: v8.18.4
  hooks:
    - id: gitleaks-system
```

### CI (full history)

```yaml
gitleaks:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@<sha>
      with:
        fetch-depth: 0              # every commit, not just the tip
        persist-credentials: false
    - name: Install gitleaks (checksum-verified release tarball)
      run: |
        curl -fsSLO https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz
        echo "<sha256 from the release's checksums.txt>  gitleaks_8.18.4_linux_x64.tar.gz" | sha256sum -c
        tar -xzf gitleaks_8.18.4_linux_x64.tar.gz gitleaks
    - run: ./gitleaks detect --redact --exit-code 1 --log-opts="--all"
```

Prove the gate fires with a canary: commit a runtime-assembled fake key to a throwaway
`mktemp -d` repo and expect `gitleaks detect --source <tmp>` to exit 1. Never push a canary.

### Alternative: TruffleHog

Pin the image by digest (a tag can move) and pass `--fail` (without it, findings still exit 0):

```bash
docker run --rm -v "$(pwd):/repo" \
  trufflesecurity/trufflehog@sha256:<digest> \
  filesystem --directory=/repo --fail   # exit 183 on findings
```

## Related Skills

- `github-actions-templates` - For GitHub Actions integration
- `gitlab-ci-patterns` - For GitLab CI integration
- `deployment-pipeline-design` - For pipeline architecture
