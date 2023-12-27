### Build and install packages
FROM python:3.10 as build-python

RUN apt-get -y update \
    # Cleanup apt cache
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_dev.txt /app/
# COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements_dev.txt
# RUN pip install -r requirements.txt

### Final image
FROM python:3.10-slim

RUN groupadd -r ecommerce && useradd -r -g ecommerce ecommerce

RUN apt-get update \
    && apt-get install -y \
    # libxml2 \
    # libssl1.1 \
    # libcairo2 \
    # libpango-1.0-0 \
    # libpangocairo-1.0-0 \
    # libgdk-pixbuf2.0-0 \
    # shared-mime-info \
    # mime-support \
    # python3-psycopg2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/media /app/static \
    && chown -R ecommerce:ecommerce /app/

COPY --from=build-python /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=build-python /usr/local/bin/ /usr/local/bin/
COPY . /app
WORKDIR /app

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN SECRET_KEY=dummy STATIC_URL=${STATIC_URL} python manage.py collectstatic --no-input

EXPOSE 8000
ENV PYTHONUNBUFFERED 1

ARG COMMIT_ID
ARG VERSION

CMD ["python", "manage.py", "runserver", "0:8000"]
# CMD ["gunicorn", "--bind", ":8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "ecommerce.asgi:application"]
