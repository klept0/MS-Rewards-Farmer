# Base image of ubuntu
FROM ubuntu:latest

EXPOSE 5900

# variables for Xvfb DBUS and docker
ENV DISPLAY=:0
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null
ENV DOCKER=1

# install dependency chrome python and pip 
RUN apt-get update && apt-get install -y \
    build-essential \
    xvfb \
    x11vnc \
    fluxbox \
    dbus \
    wget \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    jq \
    libffi-dev \
    zlib1g-dev \
    liblzma-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libnss3 \
    libxss1 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev 

RUN apt-get update && apt-get install -y xterm
#here will make a password for vnc 
RUN mkdir ~/.vnc/
RUN x11vnc -storepasswd 1234 ~/.vnc/passwd

RUN curl -sL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/trusted.gpg.d/google-chrome.gpg

# Download and install Python 3.12
WORKDIR /tmp2
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa && apt update

RUN apt install python3.12

# Download and install PIP manager for the Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3.12 get-pip.py --break-system-packages \
    && rm get-pip.py

# Add Google Chrome repository and install Chrome
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*
    
# install latest Chromedriver in /usr/bin
RUN LATEST_CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[0].url') \
    && wget -O /tmp/chromedriver.zip $LATEST_CHROMEDRIVER_URL \
    && unzip /tmp/chromedriver.zip -d /usr/bin/ \
    && mv /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# set working directory
WORKDIR /app

# copy all in the container
COPY . .

# install dependency in requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# gives perms to entrypoint
RUN chmod +x entrypoint.sh

# add script to make account.json file
COPY makeConfiguration.sh /app/makeConfiguration.sh
RUN chmod +x /app/makeConfiguration.sh


# starts the entrypoint
CMD "/app/entrypoint.sh"

#CMD ["python3", "main.py", "-v", "-l en", "-g US"]