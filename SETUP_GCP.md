# Google Cloud Console Setup

This project should run in Kevin's Google Cloud project, not from GitHub Actions and not from a local machine.

## Runtime architecture

- Cloud Run Jobs runs `monitor.py`.
- Cloud Scheduler triggers the job every morning.
- Secret Manager stores the Postmaster OAuth and SMTP values.
- Cloud Storage stores the previous-run state JSON so change detection survives between Cloud Run executions.
- Cloud Logging stores execution logs and Python errors.

## What Kevin must provide

Deployment access:
- Google Cloud project ID
- Region, for example `asia-south1` or `us-central1`
- Schedule and timezone, for example `0 9 * * *` and `Asia/Kolkata`
- Permission for the deployer to create Cloud Run Jobs, Cloud Scheduler jobs, service accounts, secrets, IAM bindings, Cloud Build builds, and Cloud Storage buckets
- Billing enabled on the Google Cloud project

Google Postmaster access:
- Google account with access to the domains in Google Postmaster Tools
- OAuth client ID
- OAuth client secret
- OAuth refresh token for the Postmaster API
- Domains to monitor, comma-separated
- DKIM selectors to check, comma-separated

Email sending:
- Sender email address
- SMTP username
- SMTP password or app password
- SMTP host
- SMTP port
- Recipient emails, comma-separated

## Prepare the env file

Create a local `.env` file from `.env.example` and fill it with Kevin's values:

```bash
cp .env.example .env
```

Example:

```text
POSTMASTER_CLIENT_ID=...
POSTMASTER_CLIENT_SECRET=...
POSTMASTER_REFRESH_TOKEN=...
POSTMASTER_SENDER_EMAIL=sender@example.com
POSTMASTER_SMTP_USERNAME=sender@example.com
POSTMASTER_SMTP_PASSWORD=...
POSTMASTER_RECIPIENTS=manager@example.com,team@example.com
POSTMASTER_DOMAINS=example.com,example.org
POSTMASTER_DKIM_SELECTORS=default,google,k1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
POSTMASTER_STATE_GCS_URI=gs://YOUR_PROJECT_ID-postmaster-monitor-state/state.json
```

Do not commit `.env`.

## Deploy from Google Cloud Shell

Open Cloud Shell in Kevin's Google Cloud project, clone the repo, and run:

```bash
chmod +x deploy-cloud-run-job.sh
./deploy-cloud-run-job.sh YOUR_PROJECT_ID YOUR_REGION postmaster-monitor .env '0 9 * * *' Asia/Kolkata
```

The script will:
- enable the required Google Cloud APIs
- create runtime and scheduler service accounts
- create or update Secret Manager secrets from `.env`
- create the Cloud Storage state bucket if needed
- build the container image
- deploy the Cloud Run Job
- grant the scheduler service account Cloud Run Invoker on the job
- create or update the Cloud Scheduler daily trigger

## Manual smoke test

After deployment, run one manual execution from Cloud Shell:

```bash
gcloud run jobs execute postmaster-monitor \
  --project YOUR_PROJECT_ID \
  --region YOUR_REGION \
  --wait
```

Then confirm:
- the job completed successfully in Cloud Run Jobs
- the email arrived
- the recipient list is correct
- the domain list and DKIM selector list are correct
- the state file exists in the configured Cloud Storage path

## Where to monitor it

- Cloud Run -> Jobs -> `postmaster-monitor` for executions
- Cloud Scheduler -> `postmaster-monitor-daily` for the daily trigger
- Cloud Logging for logs and Python errors
- Secret Manager for config values
- Cloud Storage for the state file

GitHub Actions is not part of the production runtime.
