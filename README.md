# Study School Project

Web application infrastructure based on Flask, PostgreSQL, Nginx, Docker Compose, Ansible and GitHub Actions.

The application is deployed as a multi-container environment with HTTPS termination, centralized logging and container monitoring.

## Architecture

```text
                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                              HTTP :8080
                              HTTPS :8443
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       Nginx         │
                         │  SSL termination    │
                         │  Reverse proxy      │
                         └──────────┬──────────┘
                                    │
                              HTTP :5000
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       Flask         │
                         │    Web application  │
                         └──────────┬──────────┘
                                    │
                              PostgreSQL
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      PostgreSQL     │
                         │      Database       │
                         └─────────────────────┘


       Nginx
          │
          │ Syslog UDP :514
          ▼
 ┌─────────────────┐
 │     rsyslog     │
 │  Centralized    │
 │     logging     │
 └────────┬────────┘
          │
          ▼
    remote.log


 ┌─────────────────┐
 │     cAdvisor    │
 │ Container stats │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │   Prometheus    │
 │     Metrics     │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │     Grafana     │
 │   Dashboards    │
 └─────────────────┘
```

## Components

| Component      | Purpose                             |
| -------------- | ----------------------------------- |
| Flask          | Web application                     |
| PostgreSQL     | Application database                |
| Nginx          | Reverse proxy and TLS termination   |
| rsyslog        | Centralized log collection          |
| Prometheus     | Metrics collection                  |
| cAdvisor       | Docker container metrics            |
| Grafana        | Metrics visualization               |
| Docker Compose | Container orchestration             |
| Ansible        | Server configuration and deployment |
| GitHub Actions | CI pipeline                         |

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── ansible/
│   ├── inventory.ini
│   ├── playbook.yml
│   └── secrets.yml
│
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── routes.py
│   ├── static/
│   └── templates/
│
├── monitoring/
│   └── prometheus/
│       └── prometheus.yml
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│
├── rsyslog/
│   ├── Dockerfile
│   └── rsyslog.conf
│
├── tests/
│   └── test_app.py
│
├── docker-compose-application.yml
├── docker-compose-logging.yml
├── docker-compose-monitoring.yml
├── Dockerfile
├── requirements.txt
├── run.py
└── README.md
```

## Application Stack

### Flask

The application is built with Flask and uses PostgreSQL through `psycopg2`.

The application provides:

* User registration
* Authentication
* Session management
* Logout
* Student dashboard
* Lessons
* Lesson enrollment
* Student lesson list

### PostgreSQL

PostgreSQL stores application data.

Main database entities include:

```text
users
students
teachers
lessons
lesson_enrollments
```

The PostgreSQL data is stored in a Docker named volume.

## Docker Compose

The infrastructure is split into three Compose configurations.

### Application

```bash
docker compose -f docker-compose-application.yml -p application up -d --build
```

Services:

```text
flask
postgres
nginx
```

### Logging

```bash
docker compose -f docker-compose-logging.yml -p logging up -d --build
```

Service:

```text
rsyslog
```

### Monitoring

```bash
docker compose -f docker-compose-monitoring.yml -p monitoring up -d
```

Services:

```text
cadvisor
prometheus
grafana
```

## Network Architecture

The application and logging stacks communicate through an external Docker network:

```text
logging_network
```

The network is used for Nginx → rsyslog communication.

```text
Nginx
  │
  │ UDP 514
  ▼
rsyslog
```

The monitoring stack has its own Compose network.

```text
monitoring_default
```

## Ports

| Host port | Service    | Container port | Purpose       |
| --------: | ---------- | -------------: | ------------- |
|      8080 | Nginx      |             80 | HTTP          |
|      8443 | Nginx      |            443 | HTTPS         |
|      3000 | Grafana    |           3000 | Grafana UI    |
|      8081 | cAdvisor   |           8080 | cAdvisor UI   |
|      9090 | Prometheus |           9090 | Prometheus UI |
|   514/UDP | rsyslog    |        514/UDP | Syslog        |

Flask and PostgreSQL are not exposed directly to the host.

## HTTPS

Nginx terminates TLS connections.

```text
Client
  │
  │ HTTPS
  ▼
Nginx :443
  │
  │ HTTP
  ▼
Flask :5000
```

The environment uses a self-signed certificate for HTTPS.

Certificate files:

```text
nginx/ssl/server.cert
nginx/ssl/server.key
```

For production environments, these files should be replaced with certificates issued by a trusted Certificate Authority.

## Logging

Nginx sends access logs to rsyslog over UDP:

```text
Nginx
  │
  │ syslog UDP/514
  ▼
rsyslog
  │
  ▼
/var/log/remote.log
```

Logs can be inspected with:

```bash
docker exec logging-rsyslog-1 cat /var/log/remote.log
```

Example:

```text
nginx: 172.18.0.1 - - [08/Sep/2026:06:36:08 +0000] "GET / HTTP/1.1" 200
```

## Monitoring

cAdvisor collects Docker container metrics.

```text
Docker containers
       │
       ▼
    cAdvisor
       │
       ▼
   Prometheus
       │
       ▼
    Grafana
```

Prometheus scrapes cAdvisor every 15 seconds.

Configuration:

```text
monitoring/prometheus/prometheus.yml
```

### Example metrics

CPU usage:

```promql
rate(container_cpu_usage_seconds_total{job="cadvisor",id=~"/docker/.+"}[5m]) * 100
```

Memory usage:

```promql
container_memory_usage_bytes{job="cadvisor",id=~"/docker/.+"}
```

Network receive:

```promql
rate(container_network_receive_bytes_total{job="cadvisor",id=~"/docker/.+"}[5m])
```

Network transmit:

```promql
rate(container_network_transmit_bytes_total{job="cadvisor",id=~"/docker/.+"}[5m])
```

## Accessing the Services

### Application

Open:

```text
https://<server-ip>:8443
```

Because the environment uses a self-signed certificate, the browser will display a certificate warning.

### Grafana

Open:

```text
http://<server-ip>:3000
```

### Prometheus

Open:

```text
http://<server-ip>:9090
```

### cAdvisor

Open:

```text
http://<server-ip>:8081
```

## Ansible Deployment

Ansible is used to configure the server and deploy the complete infrastructure.

The playbook performs:

* Installation of required packages
* Docker installation and configuration
* Creation of the application directory
* Repository checkout
* SSL certificate generation
* Creation of the shared Docker network
* Application deployment
* Logging deployment
* Monitoring deployment
* UFW configuration
* SSH access configuration

Inventory:

```text
ansible/inventory.ini
```

Playbook:

```text
ansible/playbook.yml
```

Secrets are stored using Ansible Vault.

### Deployment

From the control node:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become --ask-vault-pass
```

The playbook retrieves the application repository from GitHub and deploys the Docker Compose stacks.

## Ansible Vault

Sensitive variables are stored in:

```text
ansible/secrets.yml
```

The file is encrypted with Ansible Vault.

Never commit unencrypted secrets or expose the Vault password.

## Server Security

The server uses UFW with a default-deny incoming policy.

SSH access is restricted to the configured management network.

SSH password authentication is disabled.

Current SSH configuration includes:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
```

Root SSH login is disabled and authentication is performed using SSH keys.

## CI

GitHub Actions validates the project on every push to `main` and on pull requests targeting `main`.

Workflow:

```text
.github/workflows/ci.yml
```

Pipeline:

```text
Git push
   │
   ▼
GitHub Actions
   │
   ├── Build Docker image
   │
   ├── Validate application Compose
   │
   ├── Validate logging Compose
   │
   └── Validate monitoring Compose
```

Docker images are built without being pushed to a registry.

## Environment Variables

The Flask application requires:

```text
SECRET_KEY
DATABASE_URL
FLASK_HOST
FLASK_PORT
FLASK_DEBUG
```

Example:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/study_school
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=0
```

Do not commit `.env` files containing secrets.

## Manual Deployment

To deploy the application manually:

```bash
docker compose -f docker-compose-application.yml -p application up -d --build
```

Deploy logging:

```bash
docker compose -f docker-compose-logging.yml -p logging up -d --build
```

Deploy monitoring:

```bash
docker compose -f docker-compose-monitoring.yml -p monitoring up -d
```

Check running containers:

```bash
docker ps
```

Check Compose projects:

```bash
docker compose ls
```

## Troubleshooting

### Check application logs

```bash
docker compose -p application logs flask
```

### Check Nginx logs

```bash
docker compose -p application logs nginx
```

### Check PostgreSQL

```bash
docker compose -p application logs postgres
```

### Check rsyslog

```bash
docker compose -p logging logs rsyslog
```

### Check Prometheus

```bash
docker compose -p monitoring logs prometheus
```

### Check Grafana

```bash
docker compose -p monitoring logs grafana
```

### Check Docker networks

```bash
docker network ls
```

Inspect the shared logging network:

```bash
docker network inspect logging_network
```

### Check service status

```bash
docker ps
```

The PostgreSQL container should report:

```text
healthy
```

## Rebuild the Environment

The complete environment can be recreated through Ansible.

After removing the existing containers and infrastructure:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become --ask-vault-pass
```

Ansible will restore:

```text
Docker
   │
   ├── Application
   │   ├── Nginx
   │   ├── Flask
   │   └── PostgreSQL
   │
   ├── Logging
   │   └── rsyslog
   │
   └── Monitoring
       ├── cAdvisor
       ├── Prometheus
       └── Grafana
```

## Git Workflow

The main branch is:

```text
main
```

Changes are pushed to GitHub:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Every push to `main` triggers the CI workflow.

## Requirements

The server requires:

* Ubuntu Server 24.04 LTS
* Docker
* Docker Compose v2
* Git
* Ansible control node
* SSH key-based access

The deployment process installs the required server packages automatically through Ansible.

## License

This project does not currently specify a separate open-source license.

