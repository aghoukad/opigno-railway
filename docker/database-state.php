<?php

// Distinguish an empty database from a connection failure. Never reset a DB.
$timeout = (int) (getenv('DB_WAIT_TIMEOUT') ?: 180);
$deadline = time() + $timeout;
do {
  try {
    $db = new PDO(
      sprintf('mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
        getenv('MYSQLHOST'), getenv('MYSQLPORT') ?: '3306', getenv('MYSQLDATABASE')),
      getenv('MYSQLUSER'), getenv('MYSQLPASSWORD'),
      [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_TIMEOUT => 5],
    );
    echo $db->query('SHOW TABLES')->fetchColumn() === FALSE ? 'empty' : 'existing';
    exit(0);
  }
  catch (PDOException $e) {
    // Driver messages can include credentials; log only a generic retry notice.
    fwrite(STDERR, "Waiting for MySQL...\n");
    sleep(3);
  }
} while (time() < $deadline);
fwrite(STDERR, "MySQL unavailable. Check MYSQLHOST, MYSQLPORT, MYSQLDATABASE, MYSQLUSER and MYSQLPASSWORD.\n");
exit(1);
