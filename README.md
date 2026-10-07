# Opigno LMS on Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/Ys283P)

[Source repository](https://github.com/aghoukad/opigno-railway) ·
[Build validation](https://github.com/aghoukad/opigno-railway/actions/workflows/validate.yml)

Custom fork **3.2.7-patch1**, built from public Opigno 3.2.7. It upgrades Drupal
to 10.6.18, Dompdf to 3.1.6, PDF.js to 6.2.108, and the Drupal and H5P editors to
CKEditor 5. The Docker build enforces Composer and npm audits and fails if a patch
cannot be applied. The image has passed local installation and functional smoke
tests. GitHub Actions has also passed an AMD64 build, dependency audits, and a
fresh installation. Railway builds directly from this repository; no container
registry is required. The template has been created, but a live Railway deployment
has not yet been tested.

This fork records upstream source commits, dependency locks, and integration patches.
Read [MAINTENANCE.md](MAINTENANCE.md) for ownership,
security scope, behavior changes, and the **December 9, 2026 Drupal 10 support deadline**.
See [validation results](reports/validation.md) for exactly what was tested.

## Included

- PHP 8.3 and Apache, with Drupal's required PHP extensions.
- MySQL 8.4 as a separate service.
- A single `/data` volume containing public uploads, private files, temporary files,
  configuration exports, and a persistent hash salt when no variable is supplied.
- Automatic first installation with credentials supplied through environment variables.
- A database check that refuses to reinstall into any nonempty database.
- A readiness endpoint at `/healthz.php` and a Drupal cron loop every five minutes.
- Railway template variable files in `railway/` and local Docker Compose configuration.

## Build and run locally

```sh
cp .env.example .env
docker build --pull -t opigno-railway:3.2.7-patch1 .
```

Edit `.env`: set three different random passwords and the administrator email.
For example, run `openssl rand -hex 32` separately for each password. Then:

```sh
docker compose up -d
docker compose logs -f opigno
```

Open `http://localhost:8080` once installation is complete. The first installation
can take several minutes. Username defaults to `admin`; the password comes from
`OPIGNO_ADMIN_PASSWORD`. Changing that variable later does not reset an existing
account. Recreated containers reuse the database and `/data` volume.

## Deploy the Railway template

Open [Deploy on Railway](https://railway.com/deploy/Ys283P), supply
`OPIGNO_ADMIN_EMAIL`, and deploy both services. The template provisions MySQL 8.4
with `/var/lib/mysql` storage and Opigno with `/data` storage. Database passwords,
the initial administrator password, and the Drupal hash salt are generated for
each deployment. Opigno receives a public HTTPS domain routed to container port
8080; MySQL stays on Railway's private network. This template setting applies to
new deployments. Earlier deployments need their own Opigno public domain targeting
port 8080.

Wait for the image build and initial installation to finish. Sign in at
`/user/login` using `admin` and the generated `OPIGNO_ADMIN_PASSWORD` from the
Opigno service's Variables tab. Changing that variable later does not reset the
existing administrator password. Configure email delivery, backups, and a custom
domain as appropriate before inviting users.

The template is shareable by URL and is not listed in the Railway marketplace.

## Recreate or customize the Railway template

The following recipe documents the template configuration for maintainers.

1. Push this project to a GitHub repository that Railway can access. Alternatively,
   publish a tested `linux/amd64` image to your container registry and use that image
   as the Opigno service source. Never publish `.env`.
2. In [Railway's template editor](https://railway.com/workspace/templates), choose
   **New Template** and add a Docker image service named **MySQL**, using `mysql:8.4`.
3. Paste `railway/mysql.env.example` into that service's Variables → Raw Editor.
   Attach a volume at `/var/lib/mysql`. Keep MySQL private. Its default packet size
   is sufficient for the documented Opigno minimum; use at least 64 MB if overriding it.
4. Add a service named **Opigno**, sourced from your GitHub repository or published
   image. Paste `railway/opigno.env.example` into its Variables → Raw Editor. Make
   `OPIGNO_ADMIN_EMAIL` a value the template user supplies. The cross-service variable
   references assume the database service is named exactly `MySQL`.
5. Attach the Opigno volume at **`/data`**. Do not mount over `/var/www/opigno`; that
   would hide the application built into the image.
6. Enable HTTP public networking for Opigno, targeting **8080**. Set the healthcheck
   path to **`/healthz.php`** and the timeout to **900 seconds**. Leave the start and
   pre-deploy commands empty; the image handles startup after the volume is mounted.
   Use one replica and keep service sleeping disabled so cron continues to run.
7. Create the template, deploy it into a test project, and check installation,
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
- Configure and test an email delivery provider in Drupal. This image does not
  provision SMTP, an xAPI/LRS server, or live-meeting provider credentials.
- LibreOffice, ImageMagick, and video conversion tools are not included. Add and
  validate them if you require PowerPoint/video conversion features.

## Sources

- [Opigno release](https://www.drupal.org/project/opigno_lms/releases/3.2.7)
- [Opigno installation prerequisites](https://opigno.atlassian.net/wiki/spaces/OUM3/pages/2802942319/Prerequisites)
- [Railway template creation](https://docs.railway.com/templates/create)
- [Railway healthchecks](https://docs.railway.com/deployments/healthchecks)
- [Railway configuration migration](https://docs.railway.com/infrastructure-as-code)
