# We're using Alpine Edge
FROM alpine:edge

# We have to uncomment Community repo for some packages
RUN sed -e 's;^#http\(.*\)/edge/community;http\1/edge/community;g' -i /etc/apk/repositories

# install ca-certificates so that HTTPS works consistently
# other runtime dependencies for Python are installed later
RUN apk add --no-cache ca-certificates

# Installing Packages
RUN apk add --no-cache --update \
    bash \
    build-base \
    bzip2-dev \
    curl \
    coreutils \
    figlet \
    gcc \
    g++ \
    git \
    aria2 \
    util-linux \
    libevent \
    libjpeg-turbo-dev \
    jpeg-dev \
    jpeg \
    libc-dev \
    libffi-dev \
    libpq \
    libwebp-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    musl-dev \
    neofetch \
    postgresql \
    postgresql-client \
    postgresql-dev \
    wget \
    python \
    python3 \
    python-dev \
    python3-dev \
    sqlite-dev \
    sudo \
    zlib-dev \
    zip


RUN python3 -m ensurepip \
    && pip3 install --upgrade pip setuptools \
    && rm -r /usr/lib/python*/ensurepip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

#
# Clone repo and prepare working directory
#
RUN git clone 'https://github.com/HitaloSama/Hitsuki.git' /root/emilia
RUN mkdir /root/emilia/bin/
WORKDIR /root/emilia/

#
# Install requirements
#
RUN pip3 install -r requirements.txt
RUN pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
CMD ["python3","-m","emilia"]
