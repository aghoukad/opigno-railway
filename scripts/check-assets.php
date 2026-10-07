<?php

// Composer advisories do not cover all manually packaged browser libraries.
// These are checks for confirmed issues, not a comprehensive security scan.
$lock = json_decode(file_get_contents($argv[1] ?? 'composer.lock'), TRUE, 512, JSON_THROW_ON_ERROR);
$errors = [];
foreach ($lock['packages'] as $package) {
  $name = $package['name'];
  $version = ltrim($package['version'], 'v');
  if ($name === 'mozilla/pdf.js') {
    if (version_compare($version, '4.2.67', '<')) {
      $errors[] = "PDF.js $version is affected by CVE-2024-4367. Upgrade the viewer and its Drupal integration.";
    }
    if (version_compare($version, '5.6.83', '>=') && version_compare($version, '6.2.108', '<')) {
      $errors[] = "PDF.js $version is affected by CVE-2026-16633. Use a patched viewer.";
    }
  }
  if ($name === 'drupal/ckeditor') {
    $errors[] = 'The unsupported drupal/ckeditor integration remains installed. Migrate to CKEditor 5 or a verified supported integration.';
  }
}
foreach ($errors as $error) {
  fwrite(STDERR, $error . "\n");
}
exit($errors ? 1 : 0);
