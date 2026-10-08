# Validation record

Date: 2026-10-07. Local Docker Engine (OrbStack), Linux ARM64, MySQL 8.4,
PHP 8.3, Chromium browser. Disposable data only. Nothing deployed publicly.

## Passed

- Docker build from the committed dependency locks, with all upstream/local patches
  applied. Composer audit: zero advisories and zero abandoned packages. npm audit
  for the replacement H5P editor, including build dependencies: zero vulnerabilities.
- Fresh image installation into a separate empty database and new `/data` volume.
  Drupal 10.6.18 reports a successful bootstrap, connected database and `opigno_lms`
  profile. `/healthz.php` returns 200 after installation completes.
- A partial installation was detected and startup refused to overwrite the nonempty
  database. Repair/reset was performed only on the isolated test database.
- Administrator login and home page. CKEditor 5 loads on the basic-page form and
  WYSIWYG certificate form. CKEditor 4 Drupal integration is absent.
- Browser-created WYSIWYG certificate retains styled HTML and a public uploaded image.
  Entity Print/Dompdf 3 produces a valid PDF containing that image while remote
  requests, embedded PHP and PDF JavaScript remain disabled.
- PDF.js 6.2.108's full viewer loads and renders the generated one-page certificate.
  The Drupal thumbnail behavior also renders it on an Opigno dashboard page where
  legacy Angular replaces Promise. The fixture uses the formatter's DOM attributes
  and actual shipped JavaScript; it does not exercise the file-upload form.
- H5P True/False authoring with CKEditor 5.48.5.2, content save, playback and answer
  checking (1/1 score). Other H5P content types were not exercised.
- Container replacement preserves the database, login session, certificate, H5P
  activity and public-file fixture. The installer does not run again. Generated
  H5P editor assets refresh from the image during startup.
- Public upload fixture returns 200. A PHP file under public uploads returns 403.
  Direct private-file path returns 404; anonymous Drupal private download redirects
  to login. An untrusted host is rejected by the health endpoint (503).
- Manual Drupal cron completes. Browser-library vulnerability boundary checks pass.

## Login and user creation browser flow

Follow-up browser run on 2026-10-07:

- Logged out and signed in through the normal form as the administrator.
- Navigated through Catalogue, Calendar, Statistics, and People.
- Used People → Add user to create `railway.learner` (display name Railway Learner,
  user ID 2), active, with only the `authenticated` role. The account-notification
  checkbox was unchecked; the confirmation reported that no email was sent.
- Confirmed the account appeared in People, then logged out and signed in with the
  new learner's username/password. The dashboard identifies the account as Student.
- Opened Catalogue, Calendar, and the learner's profile. The learner catalogue has
  no Create new training action.
- Authenticated requests as the learner return 403 for `/admin/people`,
  `/admin/people/create`, `/statistics/dashboard`, and the private-file test fixture.
- Read-only account inspection confirms active status and no management roles.

The local learner credentials are in the ignored `.env.test-user` file, with mode
0600. This file is excluded from Git and the downloadable source archive. Public
self-registration and email verification were not exercised in this flow.

## Reproduce the automated subset

Use an isolated Compose installation created according to `README.md`, never a live
site. These checks read installation state; the optional integration script also
writes test files and a generated certificate PDF.

```sh
docker compose cp tests opigno:/tmp/opigno-tests
docker compose exec opigno mkdir -p /tmp/scripts
docker compose cp scripts/check-assets.php opigno:/tmp/scripts/check-assets.php
docker compose exec --user www-data opigno drush php:script /tmp/opigno-tests/installation.php
docker compose exec opigno php /tmp/opigno-tests/check-assets.php
docker compose exec opigno bash /usr/local/share/opigno/audit.sh
```

For `tests/integration.php`, first create a WYSIWYG certificate named **Railway smoke
certificate** in the browser. Include a `div` with class `certificate-test` and an
image pointing to `/sites/default/files/Opigno-login-image.jpg`. Then run:

```sh
docker compose exec --user www-data opigno drush --uri=http://localhost:8080 \
  php:script /tmp/opigno-tests/integration.php
```

Use your configured local port in `--uri`. Confirm the public-file fixture survives
`docker compose up -d --no-build --force-recreate opigno`. Remove the disposable
fixtures when finished. The GitHub workflow automates the image build, fresh
installation and installation/asset guards after the repository is pushed.

The [first hosted GitHub Actions run](https://github.com/aghoukad/opigno-railway/actions/runs/37703705686)
passed on 2026-10-07 for commit `59845d7`. It built the image on an AMD64 Ubuntu
runner, passed the Composer and npm audit gates, installed into a fresh MySQL
database, passed the installation and asset guards, and returned successful HTTP
responses for `/healthz.php` and `/user/login`.

The [Railway template](https://railway.com/deploy/Ys283P) was created and its
deployment page was checked in Chrome. Both services, their persistent volume
paths, and the required administrator email input were verified. Its saved
configuration provides a public service domain targeting Opigno port 8080, with
no public domain or TCP proxy for MySQL.

## Railway deployment verification — 2026-10-08

After a user-created project exposed platform-specific failures, two fixes were
applied and the existing Opigno service was rebuilt with authorization:

- Removed the Composer BuildKit cache mount, which Railway rejected because it
  requires a literal per-service cache ID. Template deployments have different IDs.
- Normalize Apache to the prefork MPM at startup, before database initialization.
  Railway's runtime loaded a conflicting MPM even though local and GitHub builds
  started correctly. A disposable-container regression check reproduces the error,
  verifies recovery, checks that PHP stays loaded, and confirms repeated startup
  preparation is safe. This check also runs in GitHub Actions.

Railway successfully built commit `dc685d7`, reused the installed Opigno database
and persistent volume, reported `Syntax OK` and `Opigno installation verified`,
started Apache, and received **HTTP 200** from `/healthz.php`. Deployment status
became **SUCCESS**. The resulting AMD64 image digest was
`sha256:0dcee7f03e97de4f166a4b15274e503a2ebc62884fbfe21e828cd65f60794c49`.

The [hosted validation run for `dc685d7`](https://github.com/aghoukad/opigno-railway/actions/runs/37705530389)
also passed: fresh AMD64 image build, dependency audits, Apache MPM regression,
fresh database installation, installation and asset checks, and HTTP checks.

The existing project was created before the template's public-domain change. When
a public domain was added afterward, the original running container rejected that
host with HTTP 400. Setting `SITE_URL` to the exact public HTTPS URL and redeploying
resolved it. `/healthz.php` and `/user/login` returned **HTTP 200** over HTTPS,
and Chrome displayed the public sign-in screen. Authentication with a production
account was not tested in this check. The first installation also logged that
sendmail was unavailable; an email provider must be configured separately.

## Remaining deployment acceptance work

Test authenticated sign-in and sessions on Railway with its real domain and proxy. Validate the course
features and H5P types you use, course enrollment/access permissions, outbound mail, backup/restore,
load, an OS/container vulnerability scan, and an existing database migration if
applicable. The local functional tests and dependency audits do not cover these.
