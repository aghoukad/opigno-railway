<?php

use Symfony\Component\HttpFoundation\Request;

$databases['default']['default'] = [
  'driver' => 'mysql',
  'namespace' => 'Drupal\\mysql\\Driver\\Database\\mysql',
  'autoload' => 'core/modules/mysql/src/Driver/Database/mysql/',
  'database' => getenv('MYSQLDATABASE'),
  'username' => getenv('MYSQLUSER'),
  'password' => getenv('MYSQLPASSWORD'),
  'host' => getenv('MYSQLHOST'),
  'port' => getenv('MYSQLPORT') ?: '3306',
  'prefix' => '',
];

$settings['hash_salt'] = getenv('DRUPAL_HASH_SALT') ?: trim(file_get_contents('/data/hash-salt'));
$settings['file_public_path'] = 'sites/default/files';
$settings['file_private_path'] = '/data/private';
$settings['file_temp_path'] = '/data/tmp';
$settings['config_sync_directory'] = '/data/config';
$settings['update_free_access'] = FALSE;
$settings['file_scan_ignore_directories'] = ['node_modules', 'bower_components'];

$hosts = ['localhost', '127.0.0.1', 'healthcheck.railway.app'];
if ($host = parse_url(getenv('SITE_URL') ?: '', PHP_URL_HOST)) {
  $hosts[] = $host;
}
if ($host = getenv('RAILWAY_PUBLIC_DOMAIN')) {
  $hosts[] = $host;
}
foreach (explode(',', getenv('DRUPAL_TRUSTED_HOSTS') ?: '') as $host) {
  if (trim($host) !== '') {
    $hosts[] = trim($host);
  }
}
$settings['trusted_host_patterns'] = array_map(
  static fn(string $host): string => '^' . preg_quote($host, '/') . '$',
  array_unique($hosts),
);

// Enable only behind Railway's edge proxy; do not trust client-supplied hosts.
if (getenv('TRUST_REVERSE_PROXY') === '1' && !empty($_SERVER['REMOTE_ADDR'])) {
  $settings['reverse_proxy'] = TRUE;
  $settings['reverse_proxy_addresses'] = [$_SERVER['REMOTE_ADDR']];
  $settings['reverse_proxy_trusted_headers'] = Request::HEADER_X_FORWARDED_PROTO | Request::HEADER_X_FORWARDED_PORT;
}

// Keep credentials and environment-specific configuration out of exported config.
$config['system.logging']['error_level'] = 'hide';
