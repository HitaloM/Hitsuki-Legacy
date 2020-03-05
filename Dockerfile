# Using Arch Linux
# Dockerfile for Hitsuki by @HitaloSama on Telegram
FROM archlinux:latest

#
# Using English as arch default language
#
RUN LANG=en_US.UTF-8

#
# Installing packages and updating the system
#
RUN pacman -Syu --noconfirm base-devel

RUN pacman -Sy --noconfirm \
    bash \
    bzip2 \
    coreutils \
    gcc \
    git \
    sudo \
    util-linux \
    libevent \
    jpeg-archive \
    libffi \
    libwebp \
    libxml2 \
    libxslt \
    linux-headers \
    musl \
    neofetch \
    postgresql \
    postgresql-client \
    postgresql-libs \
    python \
    python-pip \
    sqlite \
    zlib \
    readline

#
# Updating python
#
RUN python3 -m ensurepip \
    && pip3 install --upgrade pip setuptools \
    && rm -r /usr/lib/python*/ensurepip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

#
# Clone repo and prepare working directory
#
RUN git clone 'https://github.com/HitaloSama/Hitsuki' /root/hitsuki
RUN mkdir /root/hitsuki/bin/
RUN chmod 777 /root/hitsuki/ && chmod 777 /root/hitsuki/bin
WORKDIR /root/hitsuki/

#
# Installing requirements and updating
#
RUN pip3 install -r requirements.txt
RUN pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

RUN pip3 install python-telegram-bot==11.1.0
CMD ["python3","-m","hitsuki"]
