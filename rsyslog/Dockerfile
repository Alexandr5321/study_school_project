FROM alpine:latest

RUN apk add --no-cache rsyslog

COPY rsyslog.conf /etc/rsyslog.conf

EXPOSE 514/udp

CMD ["rsyslogd", "-n", "-f", "/etc/rsyslog.conf"]
