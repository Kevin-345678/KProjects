# Google Postmaster Daily Monitor - Detailed Google Cloud Console Setup Guide

Hi Kevin,

This guide explains exactly how to set up and run this project using **Google Cloud Console only**.

You do **not** need GitHub Actions for this version.
You can take the project as a ZIP file, upload or build it in Google Cloud, configure the required values, and run it from Google Cloud Console.

---

# 1. What this project does

This project is built to monitor the domains you manage in **Google Postmaster Tools**.

Every day, it can:
- fetch **domain reputation**
- fetch **IP reputation**
- check whether **SPF** is present
- check whether **DKIM** is present for the selectors you define
- check whether **DMARC** is present
- generate a summary report
- send the report by email

The project is designed to run automatically every morning.

---

# 2. What is inside the ZIP / project folder

The important files are:

- `monitor.py`  
  Main Python script that fetches Postmaster data, checks DNS records, and sends the email.

- `requirements.txt`  
  Python libraries required by the script.

- `Dockerfile`  
  Used to package the project into a container for Google Cloud Run.

- `cloudbuild.yaml`  
  Used by Google Cloud Build to build the container image.

- `deploy-cloud-run-job.sh`  
  Helper script for deployment if you want to deploy from Cloud Shell.

- `.env.example`  
  Example of the environment variables required.

---

# 3. Recommended deployment architecture

Use the following Google Cloud services:

1. **Cloud Run Jobs**  
   This runs the Python script in a managed container.

2. **Cloud Scheduler**  
   This triggers the job every morning automatically.

3. **Secret Manager**  
   This stores sensitive values such as credentials and passwords.

4. **Cloud Logging**  
   This shows logs and errors after every run.

This is the recommended setup because:
- it does not require your laptop to stay on
- it is visible in Google Cloud Console
- it is easier to operate later
- it is suitable for daily automation

---

# 4. Before you start

Before deployment, you need four things:

## 4.1 A Google Cloud project
You need a Google Cloud project where this job will run.

## 4.2 Google Postmaster Tools access
The Google account used must already have access to the required domains inside Google Postmaster Tools.

## 4.3 OAuth credentials for Postmaster API
You need:
- OAuth Client ID
- OAuth Client Secret
- Refresh Token

These are needed because Google Postmaster Tools API uses OAuth.

## 4.4 SMTP or email sending credentials
You need credentials for email sending.

Typical example:
- sender email address
- SMTP username
- SMTP password or app password
- SMTP host
- SMTP port

---

# 5. Information you must prepare before deployment

You must have the following values ready:

## Google Postmaster OAuth
- `POSTMASTER_CLIENT_ID`
- `POSTMASTER_CLIENT_SECRET`
- `POSTMASTER_REFRESH_TOKEN`

## Email settings
- `POSTMASTER_SENDER_EMAIL`
- `POSTMASTER_SMTP_USERNAME`
- `POSTMASTER_SMTP_PASSWORD`
- `POSTMASTER_RECIPIENTS`
- `SMTP_HOST`
- `SMTP_PORT`

## Monitoring settings
- `POSTMASTER_DOMAINS`
- `POSTMASTER_DKIM_SELECTORS`

## Example values
```text
POSTMASTER_DOMAINS=example.com,example.org
POSTMASTER_DKIM_SELECTORS=default,google,k1
POSTMASTER_RECIPIENTS=manager@company.com,deliverability@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
```

---

# 6. Step-by-step setup in Google Cloud Console

## Step 1 - Open Google Cloud Console
Open:

https://console.cloud.google.com/

Make sure you are signed in with the correct Google account.

---

## Step 2 - Select or create a project
At the top of Google Cloud Console:
1. Click the project selector.
2. Either choose an existing project or create a new project.
3. Make sure this project is the active project before continuing.

Suggested project name:
- `postmaster-monitor`

---

## Step 3 - Enable required APIs
In the Google Cloud Console search bar, search for each of the following and enable them:

1. **Cloud Run API**
2. **Cloud Build API**
3. **Artifact Registry API**
4. **Cloud Scheduler API**
5. **Secret Manager API**

How to do it:
1. Search for the API name.
2. Open the API page.
3. Click **Enable**.
4. Repeat for all required APIs.

---

## Step 4 - Open Cloud Shell
In Google Cloud Console, click the **Cloud Shell** icon in the top right corner.

Cloud Shell gives you a terminal inside Google Cloud and already includes the `gcloud` command.

Wait for Cloud Shell to start.

---

## Step 5 - Upload the ZIP file to Cloud Shell
If you are working from a ZIP file:
1. In Cloud Shell, click the three-dot menu.
2. Choose **Upload**.
3. Upload the ZIP file.
4. Unzip it inside Cloud Shell.

Example commands:

```bash
unzip your-project.zip
cd your-project-folder
```

Make sure you are now inside the project folder containing:
- `monitor.py`
- `requirements.txt`
- `Dockerfile`
- `cloudbuild.yaml`

---

## Step 6 - Verify the active project in Cloud Shell
Run:

```bash
gcloud config get-value project
```

If the project shown is not correct, set it:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

---

## Step 7 - Build the container image
Run this command from the project folder:

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions _IMAGE_URI=gcr.io/YOUR_PROJECT_ID/postmaster-monitor:latest .
```

Replace `YOUR_PROJECT_ID` with your project ID.

This step will:
- upload the project to Cloud Build
- build the Docker image
- store the image in Google Container Registry / Artifact storage path used by the build

Wait until the build completes successfully.

---

## Step 8 - Deploy the Cloud Run Job
After the image is built, run:

```bash
gcloud run jobs deploy postmaster-monitor \
  --project YOUR_PROJECT_ID \
  --region YOUR_REGION \
  --image gcr.io/YOUR_PROJECT_ID/postmaster-monitor:latest \
  --max-retries 1 \
  --task-timeout 900s
```

Example:

```bash
gcloud run jobs deploy postmaster-monitor \
  --project postmaster-monitor-123456 \
  --region asia-south1 \
  --image gcr.io/postmaster-monitor-123456/postmaster-monitor:latest \
  --max-retries 1 \
  --task-timeout 900s
```

Choose a region close to your team, for example:
- `asia-south1`
- `us-central1`
- `europe-west1`

After successful deployment, open:
- **Cloud Run**
- then the **Jobs** tab
- then open the job named `postmaster-monitor`

---

## Step 9 - Create secrets in Secret Manager
Now store the sensitive values in **Secret Manager**.

In Google Cloud Console:
1. Search for **Secret Manager**.
2. Open it.
3. Click **Create Secret**.
4. Create a separate secret for each sensitive value.

Recommended secret names:
- `postmaster-client-id`
- `postmaster-client-secret`
- `postmaster-refresh-token`
- `postmaster-sender-email`
- `postmaster-smtp-username`
- `postmaster-smtp-password`
- `postmaster-recipients`
- `postmaster-domains`
- `postmaster-dkim-selectors`
- `smtp-host`
- `smtp-port`

For each secret:
1. Enter the secret name.
2. Paste the secret value.
3. Click **Create Secret**.

Even though some values are not extremely sensitive, keeping all configuration in Secret Manager makes the setup cleaner.

---

## Step 10 - Attach secrets to the Cloud Run Job
Now connect those secrets to the job.

In Google Cloud Console:
1. Open **Cloud Run**.
2. Go to **Jobs**.
3. Open `postmaster-monitor`.
4. Click **Edit & Deploy New Revision** or **Edit**.
5. Find the **Variables & Secrets** section.
6. Add the required environment variables using Secret Manager values.

Map them like this:

| Environment Variable | Secret Name |
|---|---|
| `POSTMASTER_CLIENT_ID` | `postmaster-client-id` |
| `POSTMASTER_CLIENT_SECRET` | `postmaster-client-secret` |
| `POSTMASTER_REFRESH_TOKEN` | `postmaster-refresh-token` |
| `POSTMASTER_SENDER_EMAIL` | `postmaster-sender-email` |
| `POSTMASTER_SMTP_USERNAME` | `postmaster-smtp-username` |
| `POSTMASTER_SMTP_PASSWORD` | `postmaster-smtp-password` |
| `POSTMASTER_RECIPIENTS` | `postmaster-recipients` |
| `POSTMASTER_DOMAINS` | `postmaster-domains` |
| `POSTMASTER_DKIM_SELECTORS` | `postmaster-dkim-selectors` |
| `SMTP_HOST` | `smtp-host` |
| `SMTP_PORT` | `smtp-port` |

Save the job configuration.

---

## Step 11 - Run the job manually once
Before scheduling it, test it manually.

In Cloud Run:
1. Open the `postmaster-monitor` job.
2. Click **Execute**.
3. Wait for the run to start.
4. Open the execution details.
5. Review the logs.

Check these things:
- Did the job complete successfully?
- Did the email arrive?
- Did the report show the correct domains?
- Were SPF, DKIM, and DMARC checks correct?

---

## Step 12 - Troubleshoot if needed
If the first test run fails, check the logs.

Most common causes:

### OAuth problems
- wrong client ID or secret
- wrong refresh token
- refresh token created under the wrong Google account
- account does not have Postmaster access for the domain

### SMTP problems
- wrong SMTP username or password
- sender email does not match SMTP account
- app password required but not used
- SMTP host or port incorrect

### Domain configuration problems
- wrong domain list
- wrong DKIM selector list
- no recent Postmaster data available for the domain

### DNS check confusion
- SPF, DKIM, and DMARC are checked through DNS records
- if a DKIM selector is wrong, DKIM will show as missing even if DKIM exists under a different selector

---

## Step 13 - Create the daily scheduler
Once the manual test works, create the schedule.

In Google Cloud Console:
1. Search for **Cloud Scheduler**.
2. Open Cloud Scheduler.
3. Click **Create Job**.

Fill the form like this:

### Basic details
- Name: `postmaster-monitor-daily`
- Description: `Runs the daily Postmaster monitoring job`
- Region: choose the same region as the Cloud Run job if possible

### Schedule
Use a cron expression such as:

```text
0 9 * * *
```

This means every day at 9:00.

Choose the correct timezone for the business.

---

## Step 14 - Configure the scheduler target
There are two possible approaches.

## Recommended approach for simplicity
Use a small HTTP-triggered wrapper service if your team prefers the simplest scheduler wiring.

## Direct approach
If you are using the Cloud Run Job directly, configure Cloud Scheduler to call the Cloud Run Jobs execution API with proper authentication.

If your team wants the cleanest operator experience, use Cloud Scheduler plus a Cloud Run trigger path already approved in your cloud setup.

If needed, the deployment can later be adjusted so Cloud Scheduler hits a small Cloud Run service endpoint that starts the job.

For the current handoff, the main point is:
- the monitoring logic runs in Cloud Run
- scheduling is handled by Cloud Scheduler
- logs and executions remain visible in Google Cloud Console

---

# 7. How to check the job later

After setup, you can monitor the system entirely from Google Cloud Console.

## To see whether it ran
1. Open **Cloud Run**
2. Go to **Jobs**
3. Open `postmaster-monitor`
4. Review execution history

## To read logs
1. Open the job execution
2. View logs

Or:
1. Open **Logging**
2. Go to **Logs Explorer**
3. Filter for Cloud Run job logs

---

# 8. Operational notes

## 8.1 State tracking
The project currently includes file-based state handling in the repository version.

For a fully production-grade Cloud Run setup, long-term change tracking should later be stored in a persistent cloud store such as:
- Cloud Storage
- Firestore
- BigQuery

This is because Cloud Run containers do not keep local files between executions.

## 8.2 DKIM selectors
Make sure the selector list is correct.

Example:
```text
POSTMASTER_DKIM_SELECTORS=default,google,k1,k2
```

If the selector is wrong, DKIM may incorrectly appear missing.

## 8.3 Missing Postmaster data
Some domains may show `N/A` if:
- there is not enough recent mail volume
- Google Postmaster has not reported recent data
- the domain is not correctly available under the authorized account

---

# 9. Final checklist

Before considering the deployment complete, confirm all of the following:

- Cloud Run API enabled
- Cloud Build API enabled
- Artifact Registry API enabled
- Cloud Scheduler API enabled
- Secret Manager API enabled
- ZIP uploaded and unzipped in Cloud Shell
- container image built successfully
- Cloud Run job deployed successfully
- all secrets created in Secret Manager
- all secrets mapped into the Cloud Run job
- manual execution succeeded
- report email received
- domains and selectors verified
- Cloud Scheduler created
- daily schedule confirmed
- logs visible in Cloud Run / Logging

---

# 10. Recommended first production run

After setup is complete:
1. run the job manually once
2. confirm the output email format
3. confirm the correct recipients
4. confirm the correct domain list
5. confirm SPF, DKIM, and DMARC results look correct
6. then enable the daily scheduler

This reduces the chance of silent daily failures later.

---

# 11. Summary

The easiest way to use this project is:
1. open Google Cloud Console
2. open Cloud Shell
3. upload and unzip the project
4. build the container
5. deploy the Cloud Run job
6. add secrets through Secret Manager
7. test the job once manually
8. connect Cloud Scheduler
9. monitor future runs in Cloud Run and Logging

That is the cleanest Google Cloud Console-only setup for this project.
