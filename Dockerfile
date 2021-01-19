FROM docker.pkg.github.com/intellivoid/harukaaya/image:dockerstation

RUN git clone https://github.com/Intellivoid/HarukaAya.git -b production /data/HarukaAya

COPY ./config.yml /data/HarukaAya

WORKDIR /data/HarukaAya

CMD ["python", "-m", "haruka"]
