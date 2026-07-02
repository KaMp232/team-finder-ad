# TeamFinder

TeamFinder is a Django web application for finding teammates for study and pet projects.

The project uses template variant 2, PostgreSQL, and Docker Compose.

## Quick Start

1. Create `.env` from the example:

```bash
cp .env_example .env
```

2. Start PostgreSQL:

```bash
docker compose up -d
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply migrations and create demo data:

```bash
python manage.py migrate
python manage.py seed_demo
```

5. Run the server:

```bash
python manage.py runserver
```

Open http://localhost:8000.

## Demo User

Email: `maria@yandex.ru`

Password: `password`

## Useful Commands

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Notes For Reviewer

- The app uses PostgreSQL from `docker-compose.yml`.
- Database data is stored in the `teamfinder_ad_postgres_data` Docker volume.
- Template variant is selected by `TASK_VERSION=2`.
- The main page is `/projects/list`.
