<?php

// Exercise vulnerable boundaries and the current approved browser dependency.
$cases = [
  [['mozilla/pdf.js', 'v2.4.456'], 1],
  [['mozilla/pdf.js', '4.1.392'], 1],
  [['mozilla/pdf.js', '4.2.67'], 0],
  [['mozilla/pdf.js', '5.6.83'], 1],
  [['mozilla/pdf.js', '6.2.107'], 1],
  [['mozilla/pdf.js', '6.2.108'], 0],
  [['drupal/ckeditor', '1.0.2'], 1],
];
foreach ($cases as [[$name, $version], $expected]) {
  $file = tempnam(sys_get_temp_dir(), 'opigno-asset-');
  file_put_contents($file, json_encode(['packages' => [['name' => $name, 'version' => $version]]]));
  exec(PHP_BINARY . ' ' . escapeshellarg(__DIR__ . '/../scripts/check-assets.php') . ' ' . escapeshellarg($file) . ' 2>&1', $output, $status);
  unlink($file);
  if ($status !== $expected) {
    throw new RuntimeException("Unexpected audit result for $name $version: $status");
  }
}
echo "Browser dependency regression checks passed.\n";
