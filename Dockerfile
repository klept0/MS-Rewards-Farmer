FROM python:3.11-slim

COPY . /app

WORKDIR /app

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y chromium chromium-driver cron locales && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    chmod +x /app/docker.sh && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /etc/cron.*/* && \
    pip install --no-cache-dir -r requirements.txt

CMD ["/app/docker.sh"]
