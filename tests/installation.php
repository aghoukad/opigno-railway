<?php

// Run through Drush on an isolated test installation, never a live database.
function check(bool $condition, string $message): void {
  if (!$condition) {
    throw new RuntimeException($message);
  }
  echo "PASS: $message\n";
}

check(\Drupal::state()->get('install_task') === 'done', 'Installation completed');
check(\Drupal::moduleHandler()->moduleExists('ckeditor5'), 'CKEditor 5 enabled');
check(!\Drupal::moduleHandler()->moduleExists('ckeditor'), 'CKEditor 4 integration absent');
foreach (['basic_html', 'full_html', 'opigno_certificate_wysiwyg'] as $format) {
  check(\Drupal::config('editor.editor.' . $format)->get('editor') === 'ckeditor5', "$format uses CKEditor 5");
}
check(class_exists('H5PCore') && class_exists('H5peditor'), 'H5P runtime libraries load');
check(\Drupal::service('file_system')->realpath('private://') === '/data/private', 'Private files are outside the document root');

