<?php

use Drupal\Core\DrupalKernel;
use Symfony\Component\HttpFoundation\Request;

header('Content-Type: text/plain');
header('Cache-Control: no-store');
try {
  $autoloader = require __DIR__ . '/autoload.php';
  $request = Request::createFromGlobals();
  $kernel = DrupalKernel::createFromRequest($request, $autoloader, 'prod');
  $kernel->boot();
  require '/usr/local/share/opigno/verify-install.php';
  \Drupal::database()->query('SELECT 1');
  echo "ok\n";
}
catch (Throwable $e) {
  http_response_code(503);
  echo "not ready\n";
}
