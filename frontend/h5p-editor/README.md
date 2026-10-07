# H5P editor bundle

Builds CKEditor 5.48.5.2 for the pinned H5P editor wrapper, replacing its vulnerable
precompiled CKEditor 5.43.3.0 bundle. H5P requires a global `ClassicEditor` class and
selects plugins by name. `editor.js` supplies that interface and the nonbreaking-space
shortcut. CSS is included in the same bundle because H5P loads a single editor script.
The standard CKEditor Table plugin replaces H5P's old fork of that plugin.

```sh
npm ci --ignore-scripts
npm audit
npm run build
```

The Dockerfile runs these steps in a Node build stage and copies the result into
`vendor/h5p/h5p-editor/ckeditor/ckeditor.js`. Startup rebuilds Drupal caches so H5P
mirrors that file into persistent public assets. Do not deploy just the PHP source
without this replacement bundle.

The build selects CKEditor's GPL option and preserves bundled license notices.
H5P integration is derived from its upstream custom build and nonbreaking-space
plugin. Upstream sources: https://github.com/h5p/h5p-editor-php-library/tree/940c33d23d9e3122c8513efc1024b23e6749d787/ckeditor5
