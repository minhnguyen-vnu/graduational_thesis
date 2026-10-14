FROM python:3.8-slim
WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev redis-server && rm -rf /var/lib/apt/lists/*
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY src/ .
COPY conf.py server/conf.py
COPY entry.sh /entry.sh
EXPOSE 80
ENTRYPOINT ["/bin/bash", "/entry.sh"]
