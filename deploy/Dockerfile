FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 gomut \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin gomut
COPY . /app
RUN SECRET_KEY=build-only-static-collection-not-a-runtime-secret python -B manage.py collectstatic --noinput
USER 10001:10001
ENV DJANGO_SETTINGS_MODULE=core.settings_deploy
EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--access-logformat", "method=%(m)s status=%(s)s duration_us=%(D)s", "--error-logfile", "-", "--forwarded-allow-ips", ""]
