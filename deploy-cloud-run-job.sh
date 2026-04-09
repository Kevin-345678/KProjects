#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <PROJECT_ID> <REGION> <JOB_NAME>"
  exit 1
fi

PROJECT_ID="$1"
REGION="$2"
JOB_NAME="$3"
IMAGE_URI="gcr.io/${PROJECT_ID}/${JOB_NAME}:latest"

# Build container image with Cloud Build
 gcloud builds submit --project "$PROJECT_ID" --config cloudbuild.yaml --substitutions _IMAGE_URI="$IMAGE_URI" .

# Deploy Cloud Run Job
 gcloud run jobs deploy "$JOB_NAME" \
   --project "$PROJECT_ID" \
   --region "$REGION" \
   --image "$IMAGE_URI" \
   --max-retries 1 \
   --task-timeout 900s

cat <<EOF

Next steps:
1. Set environment variables and secrets on the job in Cloud Run.
2. Execute the job once:
   gcloud run jobs execute "$JOB_NAME" --project "$PROJECT_ID" --region "$REGION"
3. Create a Cloud Scheduler job to trigger it daily.

EOF
