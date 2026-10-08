<?php

// Run only with sendmail_path redirected to tests/mail-capture.sh.
if (!str_contains(ini_get('sendmail_path'), '/tmp/opigno-tests/mail-capture.sh')) {
  throw new RuntimeException('Refusing mail test without the local capture transport.');
}
$message = [
  'id' => 'system_resend_test',
  'module' => 'system',
  'key' => 'resend_test',
  'to' => 'learner@example.test',
  'from' => 'old@example.test',
  'subject' => 'Opigno Resend — certificat',
  'body' => ['<p>Resend integration — certificat</p>'],
  'headers' => [
    'MIME-Version' => '1.0',
    'Content-Type' => 'text/html; charset=UTF-8',
    'Return-Path' => 'old@example.test',
    'Reply-To' => 'support@example.test',
    'Bcc' => 'hidden@example.test',
  ],
  'params' => ['attachments' => [[
    'filecontent' => '%PDF-1.4 integration fixture',
    'filename' => 'resend-test.pdf',
    'filemime' => 'application/pdf',
  ]]],
];
$mailer = \Drupal::service('plugin.manager.mail')->getInstance(['module' => 'system', 'key' => 'resend_test']);
$message = $mailer->format($message);
if (!$mailer->mail($message)) {
  throw new RuntimeException('The capture transport did not accept the fixture.');
}
echo "Captured Drupal MIME email locally; no external email sent.\n";
