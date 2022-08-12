# django-crispy-idempotency

[![Build Status](https://travis-ci.org/covergenius/django-crispy-idempotency.svg?branch=master)](https://travis-ci.org/covergenius/django-crispy-idempotency)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Django Rest API idempotency at granuler(API level) and application level. Check out the project's [documentation](http://covergenius.github.io/django-crispy-idempotency/).

# Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)

# Initialize the project

Start the dev server for local development:

```bash
docker-compose up
```

Create a superuser to login to the admin:

```bash
docker-compose run --rm web ./manage.py createsuperuser
```
