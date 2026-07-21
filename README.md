# API Monitor

## Visão geral

Uma plataforma de monitoramento de APIs e serviços HTTP.

O sistema permite cadastrar endpoints e verificar periodicamente:

- disponibilidade;
- status HTTP;
- latência;
- timeouts;
- erros de conexão;
- incidentes;
- uptime.

A ideia é construir um sistema semelhante a um UptimeRobot, mas com uma
arquitetura própria baseada em API + scheduler + workers.

---

## Stack

- Python
- FastAPI
- `uv`
- PostgreSQL
- SQLAlchemy
- Alembic
- `httpx`
- Redis
- Docker Compose
- pytest

### Stack inicial

```text
FastAPI
    ↓
PostgreSQL

Scheduler
    ↓
Redis
    ↓
Workers
    ↓
httpx
    ↓
Monitored APIs
```

---

# MVP

## 1. Criar monitor

```http
POST /monitors
```

```json
{
  "name": "Minha API",
  "url": "https://example.com/health",
  "method": "GET",
  "interval_seconds": 60,
  "timeout_seconds": 10
}
```

## 2. Executar check

O sistema deve executar:

```text
Monitor due
    ↓
HTTP Request
    ↓
Measure latency
    ↓
Capture result
    ↓
Persist result
```

Cada check deve registrar:

- status HTTP;
- sucesso/falha;
- latência;
- erro;
- timeout;
- horário da execução.

## 3. Consultar monitor

```http
GET /monitors/{monitor_id}
```

Exemplo:

```json
{
  "id": "...",
  "name": "Minha API",
  "status": "up",
  "last_status_code": 200,
  "last_latency_ms": 143,
  "last_checked_at": "2026-07-20T22:00:00Z"
}
```

## 4. Histórico

```http
GET /monitors/{monitor_id}/checks
```

Suportar:

- período;
- paginação;
- filtros de status.

## 5. Incidentes

Política inicial:

```text
3 falhas consecutivas
        ↓
Incident Started
```

E:

```text
3 sucessos consecutivos
        ↓
Incident Resolved
```

---

# Modelo de domínio

## Monitor

```text
Monitor
├── id
├── name
├── url
├── method
├── interval_seconds
├── timeout_seconds
├── enabled
├── current_status
├── created_at
└── updated_at
```

## Check

```text
Check
├── id
├── monitor_id
├── status
├── status_code
├── latency_ms
├── error
├── checked_at
└── created_at
```

## Incident

```text
Incident
├── id
├── monitor_id
├── status
├── started_at
├── resolved_at
└── duration
```

---

# Arquitetura

```text
                 ┌──────────────┐
                 │   FastAPI    │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ PostgreSQL   │
                 └──────────────┘

                 ┌──────────────┐
                 │   Scheduler  │
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │    Redis     │
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │    Worker    │
                 └──────┬───────┘
                        ▼
                   HTTP APIs
```

---

# Plano de desenvolvimento

## Fase 0 --- Setup

- [ ] Criar projeto com `uv`
- [ ] Configurar FastAPI
- [ ] Configurar lint e format
- [ ] Configurar pytest
- [ ] Configurar Docker Compose
- [ ] Subir PostgreSQL
- [ ] Criar configurações por ambiente

Exemplo:

```bash
uv init
uv add fastapi uvicorn httpx sqlalchemy alembic psycopg
uv add --dev pytest ruff
```

---

## Fase 1 --- Monitor CRUD mínimo

Apesar de o projeto não ser um CRUD, precisamos de uma camada mínima
para gerenciar os monitores.

- [ ] Criar tabela `monitors`
- [ ] Criar migration
- [ ] Criar schema de criação
- [ ] Criar schema de resposta
- [ ] Criar `POST /monitors`
- [ ] Criar `GET /monitors`
- [ ] Criar `GET /monitors/{id}`
- [ ] Criar ativação/desativação

**Milestone:**

> É possível cadastrar um endpoint que deverá ser monitorado.

---

## Fase 2 --- Check Engine

- [ ] Criar cliente HTTP com `httpx`
- [ ] Implementar timeout
- [ ] Medir latência
- [ ] Capturar status HTTP
- [ ] Capturar erros de conexão
- [ ] Persistir resultado
- [ ] Criar `CheckResult`

**Milestone:**

> Um monitor pode executar um check e salvar o resultado.

---

## Fase 3 --- Scheduler

- [ ] Encontrar monitores que precisam ser executados
- [ ] Criar scheduler
- [ ] Executar checks periodicamente
- [ ] Evitar duplicação de execução
- [ ] Registrar falhas do worker

Inicialmente pode ser simples:

```text
A cada 1 segundo
    ↓
Buscar monitors due
    ↓
Executar checks
```

Depois:

```text
Scheduler
    ↓
Queue
    ↓
Worker
```

---

## Fase 4 --- Incidentes

- [ ] Contar falhas consecutivas
- [ ] Abrir incidente
- [ ] Registrar eventos do incidente
- [ ] Detectar recuperação
- [ ] Resolver incidente
- [ ] Calcular duração

---

## Fase 5 --- Métricas

- [ ] Uptime percentage
- [ ] Média de latência
- [ ] p50
- [ ] p95
- [ ] p99
- [ ] Número de incidentes
- [ ] Tempo total indisponível

---

## Fase 6 --- Alertas

- [ ] Webhook
- [ ] Email
- [ ] Discord
- [ ] Slack

O sistema deve permitir:

```text
Incident Started
        ↓
Notification
```

---

## Fase 7 --- Status Page

Criar uma página pública:

```text
/status/{slug}
```

Exemplo:

```text
API                  Operational
Dashboard            Operational
Database              Operational
```

---

# Fora do MVP

- autenticação completa;
- billing;
- frontend complexo;
- múltiplas regiões;
- IA;
- monitoramento de browser;
- monitoramento TCP/UDP.

---

# Critério de conclusão do MVP

O MVP estará concluído quando:

```text
Cadastrar monitor
        ↓
Scheduler executa check
        ↓
Resultado é persistido
        ↓
Histórico pode ser consultado
        ↓
Falhas consecutivas abrem incidente
        ↓
Recuperação resolve incidente
```

---

# Próxima evolução

A feature mais interessante depois do MVP seria:

> Detectar regressão de latência.

Exemplo:

```text
Baseline:
p95 = 250ms

Atual:
p95 = 1.8s
```

Mesmo com HTTP 200:

```text
UP
but degraded
```
