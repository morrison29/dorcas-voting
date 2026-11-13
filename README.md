# Voting system: deploy on Render

## 1. Cloudinary (for contestant photos)
Make a free account at cloudinary.com. On the dashboard, copy the **API environment variable**
(looks like `cloudinary://123456:abcd@yourcloudname`). That is your `CLOUDINARY_URL`.

## 2. Push to GitHub
Make sure `db.sqlite3` and `media/` are NOT committed (the `.gitignore` handles this).

## 3. Database on Render
New -> PostgreSQL. After it is created, copy its **Internal Database URL**.
(Free Postgres expires after 30 days, so use a paid one for the real contest.)

## 4. Web service on Render
New -> Web Service -> pick your repo, then:

- Build command: `bash build.sh`
- Start command: `gunicorn config.wsgi`

Environment variables:

| Name | Value |
|---|---|
| `DATABASE_URL` | the Internal Database URL from step 3 |
| `SECRET_KEY` | any long random text (e.g. run `python -c "import secrets;print(secrets.token_urlsafe(50))"`) |
| `CLOUDINARY_URL` | from step 1 |
| `DJANGO_SUPERUSER_USERNAME` | your admin username |
| `DJANGO_SUPERUSER_PASSWORD` | a strong password |
| `DJANGO_SUPERUSER_EMAIL` | your email |
| `PYTHON_VERSION` | `3.12.8` |

Deploy. Then open `https://your-app.onrender.com/admin/`, log in, and:
set the bank account in **Contest**, add your two **Contestants** with photos.

## Run locally
```
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
With no environment variables set it uses SQLite and local photo storage.
