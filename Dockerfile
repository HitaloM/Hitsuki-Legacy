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
    curl \
    gcc \
    git \
    libffi-dev \
    libjpeg \
    libjpeg-turbo-dev \
    libwebp-dev \
    linux-headers \
    musl \
    musl-dev \
    neofetch \
    rsync \
    zlib \
    zlib-dev
    postgresql \
    postgresql-client \
    postgresql-dev \
    python \
    python3 \
    python-dev \
    python3-dev \
    sqlite-dev \
    sudo


RUN python3 -m ensurepip \
    && pip3 install --upgrade pip setuptools \
    && rm -r /usr/lib/python*/ensurepip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

#
# Clone repo and prepare working directory
#
RUN git clone 'https://github.com/HitaloSama/Hitsuki.git' /root/hitsuki
RUN mkdir /root/hitsuki/bin/
WORKDIR /root/hitsuki/

#
# Install requirements
#
RUN pip3 install -r requirements.txt
RUN pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
CMD ["python3","-m","emilia"]
