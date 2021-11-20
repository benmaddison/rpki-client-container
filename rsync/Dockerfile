FROM alpine:latest

WORKDIR /root

RUN apk update && \
    apk upgrade && \
    apk add --no-cache rsync

RUN mkdir -p data

COPY ./rsyncd.conf /etc/

ENTRYPOINT ["/usr/bin/rsync", "--no-detach", "--daemon", "--config", "/etc/rsyncd.conf"]
