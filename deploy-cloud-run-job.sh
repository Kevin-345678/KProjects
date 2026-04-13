#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <PROJECT_ID> <REGION> <JOB_NAME> <ENV_FILE> [SCHEDULE] [TIME_ZONE]"
  echo "Example: $0 my-gcp-project asia-south1 postmaster-monitor .env '0 9 * * *' Asia/Kolkata"
  exit 1
fi

PROJECT_ID="$1"
REGION="$2"
JOB_NAME="$3"
ENV_FILE="$4"
SCHEDULE="${5:-0 9 * * *}"
TIME_ZONE="${6:-Asia/Kolkata}"
IMAGE_URI="gcr.io/${PROJECT_ID}/${JOB_NAME}:latest"
SCHEDULER_NAME="${JOB_NAME}-daily"

REQUIRED_ENV_VARS=(
  POSTMASTER_CLIENT_ID
  POSTMASTER_CLIENT_SECRET
  POSTMASTER_REFRESH_TOKEN
  POSTMASTER_SENDER_EMAIL
  POSTMASTER_SMTP_USERNAME
  POSTMASTER_SMTP_PASSWORD
  POSTMASTER_RECIPIENTS
  SMTP_HOST
  SMTP_PORT
)

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found: $ENV_FILE"
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

missing_vars=()
for name in "${REQUIRED_ENV_VARS[@]}"; do
  if [ -z "${!name:-}" ]; then
    missing_vars+=("$name")
  fi
done

if [ "${#missing_vars[@]}" -gt 0 ]; then
  echo "Missing required values in $ENV_FILE:"
  printf '  %s\n' "${missing_vars[@]}"
  exit 1
fi

RUNTIME_SERVICE_ACCOUNT="${POSTMASTER_RUNTIME_SERVICE_ACCOUNT:-${JOB_NAME}-runner@${PROJECT_ID}.iam.gserviceaccount.com}"
SCHEDULER_SERVICE_ACCOUNT="${POSTMASTER_SCHEDULER_SERVICE_ACCOUNT:-${JOB_NAME}-scheduler@${PROJECT_ID}.iam.gserviceaccount.com}"

if [ -n "${POSTMASTER_STATE_GCS_URI:-}" ]; then
  STATE_BUCKET="${POSTMASTER_STATE_GCS_URI#gs://}"
  STATE_BUCKET="${STATE_BUCKET%%/*}"
  if [ "$STATE_BUCKET" = "$POSTMASTER_STATE_GCS_URI" ] || [ -z "$STATE_BUCKET" ]; then
    echo "POSTMASTER_STATE_GCS_URI must look like gs://bucket/path/state.json"
    exit 1
  fi
else
  STATE_BUCKET="${POSTMASTER_STATE_BUCKET:-${PROJECT_ID}-${JOB_NAME}-state}"
  POSTMASTER_STATE_GCS_URI="gs://${STATE_BUCKET}/state.json"
fi

secret_name_for_env_var() {
  echo "$1" | tr '[:upper:]_' '[:lower:]-'
}

ensure_service_account() {
  local email="$1"
  local account_id="${email%%@*}"
  if gcloud iam service-accounts describe "$email" --project "$PROJECT_ID" >/dev/null 2>&1; then
    return
  fi
  gcloud iam service-accounts create "$account_id" \
    --project "$PROJECT_ID" \
    --display-name "$account_id"
}

upsert_secret_version() {
  local name="$1"
  local value="$2"
  local secret_name
  local new_version
  secret_name="$(secret_name_for_env_var "$name")"

  if ! gcloud secrets describe "$secret_name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    new_version="$(printf "%s" "$value" | gcloud secrets create "$secret_name" \
      --project "$PROJECT_ID" \
      --replication-policy="automatic" \
      --data-file=- \
      --format="value(name)")"
  else
    new_version="$(printf "%s" "$value" | gcloud secrets versions add "$secret_name" \
      --project "$PROJECT_ID" \
      --data-file=- \
      --format="value(name)")"
  fi

  gcloud secrets versions list "$secret_name" \
    --project "$PROJECT_ID" \
    --filter="state:enabled" \
    --format="value(name)" |
    while read -r version_name; do
      if [ -n "$version_name" ] && [ "$version_name" != "$new_version" ]; then
        gcloud secrets versions destroy "$version_name" \
          --project "$PROJECT_ID" \
          --quiet >/dev/null
      fi
    done
}

echo "Enabling required Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  --project "$PROJECT_ID"

echo "Creating service accounts..."
ensure_service_account "$RUNTIME_SERVICE_ACCOUNT"
ensure_service_account "$SCHEDULER_SERVICE_ACCOUNT"

echo "Creating state bucket if needed..."
if ! gcloud storage buckets describe "gs://${STATE_BUCKET}" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${STATE_BUCKET}" \
    --project "$PROJECT_ID" \
    --location "$REGION"
fi

echo "Granting runtime permissions..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${RUNTIME_SERVICE_ACCOUNT}" \
  --role "roles/secretmanager.secretAccessor" \
  --condition=None >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${STATE_BUCKET}" \
  --member "serviceAccount:${RUNTIME_SERVICE_ACCOUNT}" \
  --role "roles/storage.objectAdmin" >/dev/null

echo "Creating or updating Secret Manager values..."
secret_mappings=()
for name in "${REQUIRED_ENV_VARS[@]}"; do
  upsert_secret_version "$name" "${!name}"
  secret_mappings+=("${name}=$(secret_name_for_env_var "$name"):latest")
done
SET_SECRETS="$(IFS=,; echo "${secret_mappings[*]}")"

echo "Building container image..."
gcloud builds submit \
  --project "$PROJECT_ID" \
  --config cloudbuild.yaml \
  --substitutions _IMAGE_URI="$IMAGE_URI" \
  .

echo "Deploying Cloud Run Job..."
gcloud run jobs deploy "$JOB_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --image "$IMAGE_URI" \
  --service-account "$RUNTIME_SERVICE_ACCOUNT" \
  --set-secrets "$SET_SECRETS" \
  --set-env-vars "POSTMASTER_STATE_GCS_URI=${POSTMASTER_STATE_GCS_URI}" \
  --max-retries 1 \
  --task-timeout 900s

echo "Granting scheduler permission to execute the Cloud Run Job..."
gcloud run jobs add-iam-policy-binding "$JOB_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --member "serviceAccount:${SCHEDULER_SERVICE_ACCOUNT}" \
  --role "roles/run.invoker" >/dev/null

RUN_URI="https://run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB_NAME}:run"

echo "Creating or updating Cloud Scheduler job..."
if gcloud scheduler jobs describe "$SCHEDULER_NAME" --project "$PROJECT_ID" --location "$REGION" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "$SCHEDULER_NAME" \
    --project "$PROJECT_ID" \
    --location "$REGION" \
    --schedule "$SCHEDULE" \
    --time-zone "$TIME_ZONE" \
    --uri "$RUN_URI" \
    --http-method POST \
    --oauth-service-account-email "$SCHEDULER_SERVICE_ACCOUNT" \
    --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform"
else
  gcloud scheduler jobs create http "$SCHEDULER_NAME" \
    --project "$PROJECT_ID" \
    --location "$REGION" \
    --schedule "$SCHEDULE" \
    --time-zone "$TIME_ZONE" \
    --uri "$RUN_URI" \
    --http-method POST \
    --oauth-service-account-email "$SCHEDULER_SERVICE_ACCOUNT" \
    --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform"
fi

cat <<EOF

Deployment configured.

Cloud Run Job:
  $JOB_NAME

Cloud Scheduler:
  $SCHEDULER_NAME
  $SCHEDULE ($TIME_ZONE)

State file:
  $POSTMASTER_STATE_GCS_URI

Run one manual smoke test:
  gcloud run jobs execute "$JOB_NAME" --project "$PROJECT_ID" --region "$REGION" --wait

EOF
