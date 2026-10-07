<?php

require __DIR__ . '/installation.php';

$account = \Drupal\user\Entity\User::load(1);
$switcher = \Drupal::service('account_switcher');
$switcher->switchTo($account);
try {
  $certificates = \Drupal::entityTypeManager()->getStorage('opigno_certificate')->loadByProperties(['label' => 'Railway smoke certificate']);
  $certificate = reset($certificates);
  check((bool) $certificate, 'Browser-created certificate saved');
  check(str_contains($certificate->body->value, 'certificate-test'), 'Certificate HTML survives editor submission');
  $engine = \Drupal::service('plugin.manager.entity_print.print_engine')->createInstance('dompdf');
  $uri = \Drupal::service('entity_print.print_builder')->savePrintable([$certificate], $engine, 'private', 'smoke-certificate.pdf');
  $pdf = file_get_contents($uri);
  check(str_starts_with($pdf, '%PDF-'), 'Entity Print generates a PDF using Dompdf 3');
  check(str_contains($pdf, '/Subtype /Image'), 'Certificate PDF includes its local image');
  file_put_contents('public://persistence-test.txt', 'opigno-persistence-test');
  file_put_contents('private://private-test.txt', 'private-test');
  file_put_contents('public://execution-test.php', '<?php echo "EXECUTED";');
}
finally {
  $switcher->switchBack();
}
