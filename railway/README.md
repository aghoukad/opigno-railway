# Railway template reference

[Back to the quick start](../README.md)

## Recreate or customize the template

The following recipe documents the template configuration for maintainers.

1. Push this project to a GitHub repository that Railway can access. Alternatively,
   publish a tested `linux/amd64` image to your container registry and use that image
   as the Opigno service source. Never publish `.env`.
2. In [Railway's template editor](https://railway.com/workspace/templates), choose
   **New Template** and add a Docker image service named **MySQL**, using `mysql:8.4`.
3. Paste [mysql.env.example](mysql.env.example) into that service's Variables → Raw Editor.
   Attach a volume at `/var/lib/mysql`. Keep MySQL private. Its default packet size
   is sufficient for the documented Opigno minimum; use at least 64 MB if overriding it.
4. Add a service named **Opigno**, sourced from your GitHub repository or published
   image. Paste [opigno.env.example](opigno.env.example) into its Variables → Raw Editor. Make
   `OPIGNO_ADMIN_EMAIL` a value the template user supplies. The cross-service variable
   references assume the database service is named exactly `MySQL`.
   Mark `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `RESEND_FROM_NAME` optional;
   leave the key and sender address blank as placeholders.
5. Attach the Opigno volume at **`/data`**. Do not mount over `/var/www/opigno`; that
   would hide the application built into the image.
6. Enable HTTP public networking for Opigno, targeting **8080**. Set the healthcheck
   path to **`/healthz.php`** and the timeout to **900 seconds**. Leave the start and
   pre-deploy commands empty; the image handles startup after the volume is mounted.
   Use one replica and keep service sleeping disabled so cron continues to run.
7. Add a description to every variable and a transparent icon to each service.
   Check that Railway shows **4/4 Template Guidelines** before sharing.
8. Create the template, deploy it into a test project, and check installation,
   sign-in, uploads, private download permissions, course delivery, certificates,
   and persistence across a redeploy. Only then share or publish the template.

`${{secret(...)}}` expressions belong in the **template editor**. For a manually
created live project, set actual randomly generated secrets instead. The supplied
MySQL variable names are for the raw `mysql:8.4` service described here. If you use
Railway's existing MySQL template instead, map its exported `MYSQLHOST`, `MYSQLPORT`,
`MYSQLDATABASE`, `MYSQLUSER`, and `MYSQLPASSWORD` variables to Opigno.

The service automatically uses `RAILWAY_PUBLIC_DOMAIN` for its site URL and trusted
host. For a custom domain, set `SITE_URL=https://learning.example.com`. Additional
allowed hostnames go in `DRUPAL_TRUSTED_HOSTS`, comma-separated without schemes.
`TRUST_REVERSE_PROXY=1` is for Railway's edge proxy; it trusts forwarded protocol and
port from the immediate peer. Leave it unset for direct local HTTP access.

If you add a public domain after a service has already started, redeploy the
service so its container receives the updated Railway domain variable. If Drupal
shows **"The provided host name is not valid for this server"**, set `SITE_URL`
to the exact public URL (for example, `https://your-service.up.railway.app`) and
apply the variable change/redeploy. The URL's hostname is automatically added to
Drupal's allowed hosts. Keep additional aliases in `DRUPAL_TRUSTED_HOSTS`;
do not disable host validation or allow every hostname.

Railway's current documentation says new services cannot adopt the deprecated
[`railway.json`/`railway.toml` format](https://docs.railway.com/config-as-code). This repository uses the template editor. For infrastructure as code, Railway
now provides `.railway/railway.ts`; that is a separate CLI-managed workflow.

For a registry image, build the Railway architecture explicitly (the local smoke
image was tested on ARM64):

```sh
docker buildx build --platform linux/amd64 --pull \
  --tag ghcr.io/YOUR_ORG/opigno-railway:3.2.7-patch1 --push .
```

Replace `YOUR_ORG` and authenticate to your registry first. Choose either the GitHub
source build or the published image in Railway; both use this Dockerfile.

The Dockerfile intentionally avoids BuildKit cache mounts. Railway requires a
literal service ID in each [cache mount ID](https://docs.railway.com/builds/dockerfiles#cache-mounts),
while every template deployment creates a different service ID. Composer uses a
temporary cache that is removed in the same build layer instead.

## Service icons

| Service | Transparent icon |
| --- | --- |
| Opigno | [Opigno theme favicon](https://git.drupalcode.org/project/aristotle/-/raw/3.2.7/favicon.ico) |
| MySQL | [Railway MySQL icon](https://devicons.railway.com/i/mysql.svg) |

## Email transport details

PHP `mail()` uses the included Resend HTTPS transport. Keep Drupal configured with
the **PHP Mail sender / Mime Mail formatter**; no additional module is required.
See the [Resend setup instructions](../README.md#email-with-resend) for variables.

The transport preserves plain text, HTML, Unicode subjects, Reply-To, Cc/Bcc,
attachments and inline image content IDs. It always sends from the configured
verified address; Resend manages the bounce/Return-Path address. Existing Drupal
email templates and the notification queue remain in use. The API key is read only
from the environment and is never written to Drupal configuration or transport logs.

Transient API/network failures are retried up to three times with the same
[Resend idempotency key](https://resend.com/docs/dashboard/emails/idempotency-keys).
After that, PHP receives a failure. The transport does not add a durable queue for
ordinary synchronous Drupal mail, and separate Drupal queue attempts are separate
submissions. Check the Resend dashboard for acceptance, delivery and bounces, and
verify an account notification/password-reset email to a recipient you control
before relying on mail. Resend's sending quotas, recipient limits, attachment type
restrictions and 40 MB email limit apply. No real delivery is tested with placeholders.

## Operations

- Back up both the MySQL database and `/data` and test restoring them together.
- Keep the hash salt stable across deploys. Do not regenerate template secrets in an
  existing installation. Preserve the application volume during rebuilds.
- A partial installation causes startup to fail. Restore a known-good backup or
  investigate the database; the entrypoint never automatically wipes or repairs it.
- Run reviewed database updates explicitly after taking a backup. For example,
  `docker compose exec --user www-data opigno drush updatedb -y`, then
  `docker compose exec --user www-data opigno drush cache:rebuild`.
- Test a fresh installation and an upgrade against a copy of production before
  changing the image. Code deployment rebuilds caches and refreshes generated
  H5P assets; it does not automatically run database updates.
- `CRON_INTERVAL` is in seconds; `CRON_ENABLED=0` disables the in-container scheduler.
  `DB_WAIT_TIMEOUT` defaults to 180 seconds. Run `drush cron` as `www-data` for manual
  maintenance. Railway's deployment healthcheck is not continuous monitoring.
- Configure and test Resend before inviting learners. The image does not provision
  a Resend account, an xAPI/LRS server, or live-meeting provider credentials.
- LibreOffice, ImageMagick, and video conversion tools are not included. Add and
  validate them if you require PowerPoint/video conversion features.

