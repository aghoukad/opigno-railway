# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS editor
WORKDIR /build
COPY frontend/h5p-editor/package.json frontend/h5p-editor/package-lock.json ./
RUN npm ci --ignore-scripts && npm audit
COPY frontend/h5p-editor/editor.js frontend/h5p-editor/build.mjs ./
RUN npm run build

FROM php:8.3-apache-bookworm AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git unzip patch gosu \
      libfreetype6-dev libjpeg62-turbo-dev libpng-dev libwebp-dev \
      libicu-dev libzip-dev libonig-dev libxml2-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j"$(nproc)" bcmath gd intl mbstring mysqli pdo_mysql zip opcache \
    && a2enmod rewrite headers expires \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2.10.3 /usr/bin/composer /usr/local/bin/composer
ENV COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_MEMORY_LIMIT=-1
WORKDIR /var/www/opigno

FROM base AS security
COPY composer.json composer.lock ./
COPY scripts/check-assets.php scripts/audit.sh /usr/local/share/opigno/
RUN composer --no-plugins validate --no-check-publish --no-check-all --strict \
    && bash /usr/local/share/opigno/audit.sh

FROM security AS dependencies
COPY patches ./patches
# Railway cache mount IDs must contain the deployment's service ID. Templates
# create a new service ID each time, so keep this build portable without a mount.
RUN COMPOSER_CACHE_DIR=/tmp/composer-cache composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader \
    && rm -rf /tmp/composer-cache

FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=dependencies /var/www/opigno /var/www/opigno
# Replace H5P's bundled editor, which is outside Composer advisory coverage.
COPY --from=editor /build/dist/ckeditor.js /var/www/opigno/vendor/h5p/h5p-editor/ckeditor/ckeditor.js
COPY frontend/h5p-editor/package.json frontend/h5p-editor/package-lock.json /usr/local/share/opigno/h5p-editor/
COPY docker/php.ini /usr/local/etc/php/conf.d/opigno.ini
COPY docker/apache.conf /etc/apache2/sites-available/000-default.conf
COPY docker/settings.php /var/www/opigno/web/sites/default/settings.php
COPY docker/healthz.php /var/www/opigno/web/healthz.php
COPY docker/database-state.php docker/verify-install.php /usr/local/share/opigno/
COPY scripts/check-assets.php scripts/audit.sh /usr/local/share/opigno/
COPY docker/entrypoint.sh /usr/local/bin/opigno-entrypoint
COPY docker/cron.sh /usr/local/bin/opigno-cron
COPY docker/apache-prepare.sh /usr/local/bin/opigno-apache-prepare
COPY docker/resend-mail.py /usr/local/bin/opigno-resend-mail
RUN chmod 0755 /usr/local/bin/opigno-entrypoint /usr/local/bin/opigno-cron /usr/local/bin/opigno-apache-prepare /usr/local/bin/opigno-resend-mail \
    && mkdir -p web/sites/default \
    && rm -rf web/sites/default/files \
    && ln -s /data/public web/sites/default/files \
    && chmod 0444 web/sites/default/settings.php \
    && chmod 0755 web/sites/default
ENV PORT=8080 PATH="/var/www/opigno/vendor/bin:${PATH}"
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=15m --retries=3 \
    CMD curl --fail --silent "http://127.0.0.1:${PORT}/healthz.php" || exit 1
ENTRYPOINT ["opigno-entrypoint"]
CMD ["apache2-foreground"]
