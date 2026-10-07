<?php

if (\Drupal::state()->get('install_task') !== 'done'
  || \Drupal::config('core.extension')->get('profile') !== 'opigno_lms') {
  throw new RuntimeException('The database does not contain a completed Opigno installation. Refusing to reinstall it.');
}
