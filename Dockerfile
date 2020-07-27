FROM registry.gitlab.com/harukanetwork/oss/harukaaya:dockerstation

RUN git clone "https://github.com/HitaloSama/Hitsuki" -b beta /data/Hitsuki

COPY ./config.yml /data/Hitsuki

WORKDIR /data/Hitsuki

CMD ["python", "-m", "hitsuki"]
