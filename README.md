# Study School Infrastructure

Учебный проект инфраструктуры веб-приложения.

**Стек:** Flask, PostgreSQL, Nginx, Docker Compose, Ansible, Prometheus, Grafana, GitHub Actions

### Что сделано

- Многоконтейнерная инфраструктура (Flask + Postgres + Nginx)
- HTTPS через Nginx (reverse proxy + SSL)
- Централизованные логи (Nginx → rsyslog)
- Мониторинг: cAdvisor → Prometheus → Grafana
- Автоматическое развёртывание через Ansible
- CI на GitHub Actions

### Структура
application/   — Flask + PostgreSQL + Nginx
logging/       — rsyslog
monitoring/    — cAdvisor + Prometheus + Grafana
ansible/       — плейбук для развёртывания
text### Запуск

**Вручную:**
```bash
docker compose -f docker-compose-application.yml -p application up -d --build
docker compose -f docker-compose-logging.yml -p logging up -d --build
docker compose -f docker-compose-monitoring.yml -p monitoring up -d
Через Ansible:
Bashcd ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become --ask-vault-pass
```

####Полезные команды
Bashdocker compose ls
docker compose -p application logs flask
docker exec logging-rsyslog-1 cat /var/log/remote.log
