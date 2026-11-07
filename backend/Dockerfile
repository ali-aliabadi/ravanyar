FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/venv PATH=/venv/bin:$PATH
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY manage.py ./
COPY src ./src
# collectstatic imports settings, so it gets throwaway values; the real ones come at runtime.
RUN DJANGO_SECRET_KEY=build DJANGO_ALLOWED_HOSTS=x POSTGRES_DB=x POSTGRES_USER=x \
    POSTGRES_PASSWORD=x POSTGRES_HOST=x KAVENEGAR_API_KEY=x RAVANYAR_PRELAUNCH=1 \
    RAVANYAR_MASTER_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    RAVANYAR_BLIND_INDEX_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py collectstatic --noinput
RUN useradd --system app
USER app
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
EXPOSE 8000
CMD ["uvicorn", "config.asgi:application", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
