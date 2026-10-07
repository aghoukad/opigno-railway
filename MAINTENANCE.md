# Maintaining the Opigno fork

Baseline: `3.2.7-patch1`, checked 2026-10-07. This repository records the upstream
source references, patched dependency constraints, local patches, Composer lockfile,
and a separately built H5P editor. It does not depend on access to paid Opigno packages.

## Resolved dependency findings

| Component | Baseline used here | Integration work |
| --- | --- | --- |
| Drupal | 10.6.18 | Current compatible Drupal 10 release; Twig compatibility patches |
| Dompdf | 3.1.6 | Removed the old filesystem-validation bypass; remote requests, embedded PHP and PDF JavaScript disabled; same-origin certificate images resolve to local files |
| PDF.js | 6.2.108 | ES-module worker and viewer paths; asynchronous Drupal formatter loading and legacy Angular Promise compatibility; evaluation disabled in formatters |
| Drupal editors | Core CKEditor 5 | Fresh-install basic/full HTML and certificate configurations migrated; CKEditor 4 dependencies removed |
| H5P editor | CKEditor 5.48.5.2 | Rebuilt from locked npm packages; original bundled editor replaced; modern standard table plugin |
| H5P PHP integration | Core 1.28 + pinned editor source | Hub reset callback and storage API compatibility patches |

The public Dompdf 2.0.8 dependency had six current advisories. PDF.js 2.4.456 was
affected by CVE-2024-4367; 6.2.108 also avoids the later CVE-2026-16633. H5P's newer
source still bundled CKEditor 5.43.3.0, so merely adopting that source was insufficient.
The replacement build avoids the current CKEditor clipboard, HTML support and engine
advisories. No Composer advisory ignores or security-blocking bypasses are configured.

The Docker build fails if the Composer audit, npm audit, known browser-library checks,
or patch application fails. npm checks include build dependencies. The build gates
query current advisory databases when executed; use `--no-cache` for a fresh audit
rather than relying on an old successful Docker layer.

## Source and patch ownership

- Original Composer project: Opigno commit `d86a0b629a7db76834bd091f134e92331cb5421e`.
- Distribution: Opigno commit `d60e7e3b7935dbcf037536dd1b775bc603192660`, with fork
  dependency metadata in `composer.json` and `patches/profile-ckeditor5.patch`.
- H5P editor source: `940c33d23d9e3122c8513efc1024b23e6749d787` from
  `h5p/h5p-editor-php-library`. `frontend/h5p-editor/` replaces its compiled editor;
  the H5P wrapper remains at that source reference.
- Local integration changes are in `patches/`. Most original Opigno patches remain
  in the package metadata. Obsolete calendar/H5P fixes were removed where the locked
  package already includes them. The unsafe old Dompdf helper patch was removed.
- Composer locks development/pre-release contributed modules where public Opigno
  requires them. A lockfile pins their code; it does not create upstream support.
- Preserve upstream license notices when publishing. The H5P editor build selects
  CKEditor's GPL distribution. Individual dependencies retain their own licenses.

This repository is the custom fork. Editing generated `web/` or `vendor/` files alone
will not survive a rebuild: record every change in a patch, dependency lock, or the
frontend build sources.

## Behavior and migration boundaries

This baseline targets a **new installation**. It has no automatic migration of an
existing Opigno database's CKEditor 4 configuration. For an existing site, work on a
restored copy, migrate each text format and certificate, run reviewed database updates,
and test existing content before switching traffic.

The old certificate background/font CKEditor 4 buttons are removed. Certificate HTML
can use the CKEditor 5 source editor; supported div/span/p/img style and class attributes
are retained. A certificate with styled HTML and an uploaded image was verified.
Externally hosted certificate images are intentionally unavailable to Dompdf: upload
assets locally. H5P uses the current standard CKEditor table implementation; complex
legacy table layouts need content-specific review. The H5P rich-text toolbar defaults
to English; Drupal/H5P interface translations remain separate.

Only a True/False H5P activity was exercised end to end. All other content types, SCORM,
commerce, learner enrollment/completion flows, external integrations, and imported
course libraries require acceptance testing for the features you use. Downloaded H5P
content libraries live in the volume and are not fully covered by Composer/npm audits.

## Release procedure

1. Work on a branch and back up a representative test database and `/data`.
2. Review Drupal, Opigno, Dompdf, PDF.js, H5P and CKEditor advisories. Update the fork
   constraints and locks deliberately; never remove a failing audit to force a release.
3. Build with `docker build --pull --no-cache -t opigno-railway:NEW_TAG .` to refresh
   base packages, run both audits, and prove patches apply to clean dependencies.
4. Test an empty database installation and a restored production database. Follow
   `reports/validation.md`, test your course/content types, and run an OS/container
   vulnerability scan for the target architecture. Record findings and image digest.
5. Publish an immutable tag/digest, back up production, deploy one replica, and run
   any reviewed `drush updatedb` explicitly. Check health, login, cron, and content.
6. Roll back code together with a compatible database/files backup if an update fails.

Rebuild for security updates regularly. The startup process refreshes caches and
mirrored H5P assets; it does not update dependencies or database schemas at runtime.
The included GitHub workflow can run the build and fresh-install checks after this
repository is pushed; it does not publish images or deploy Railway.

**Drupal 10 reaches end of life on December 9, 2026.** Plan and complete a Drupal 11
port before that date. Upgrading the Opigno modules and contributed dependencies to
Drupal 11 is separate from this tested Drupal 10 baseline; do not simply change the
core constraint and assume compatibility.

## Evidence and limits

`reports/composer-audit.json` and `reports/npm-audit.json` report zero known advisories
for their respective locked dependency graphs on the recorded date. The browser asset
check covers known PDF.js vulnerabilities and the removed Drupal CKEditor 4 module.
These results do not mean the full legacy application, OS image, or every downloaded
H5P library has been independently security-audited. No Railway deployment, AMD64
runtime test, load test, or existing-site data migration was performed locally.

## Primary references

- [Opigno public release](https://www.drupal.org/project/opigno_lms/releases/3.2.7)
- [Dompdf advisories](https://github.com/dompdf/dompdf/security/advisories)
- [PDF.js 2024 advisory](https://github.com/mozilla/pdf.js/security/advisories/GHSA-wgrm-67xf-hhpq)
- [PDF.js 2026 advisory](https://github.com/mozilla/pdf.js/security/advisories/GHSA-hq66-cqwq-w95j)
- [CKEditor 4 Drupal status](https://www.drupal.org/project/ckeditor)
- [CKEditor 5 advisories](https://github.com/ckeditor/ckeditor5/security/advisories)
- [H5P editor source](https://github.com/h5p/h5p-editor-php-library)
- [Drupal release and support schedule](https://www.drupal.org/about/core/policies/core-release-cycles/schedule)
