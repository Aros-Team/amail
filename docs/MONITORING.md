# Monitorización del Servicio de Email (Amail)

Este documento describe el sistema de monitorización implementado para el servicio de email con Resend.

## Tabla de Contenidos

1. [Logging Estructurado](#logging-estructurado)
2. [Métricas Prometheus](#métricas-prometheus)
3. [Health Checks](#health-checks)
4. [Reintentos](#reintentos)
5. [Dashboards](#dashboards)
6. [Alertas](#alertas)
7. [Consulta de Logs](#consulta-de-logs)

---

## Logging Estructurado

### Formato JSON

Todos los logs se generan en formato JSON con la siguiente estructura:

```json
{
  "request_id": "uuid-unico",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event": "email_send_start|email_send_success|email_send_failure|email_retry",
  "level": "info|warning|error",
  "to": "destinatario@ejemplo.com",
  "subject": "Asunto del email",
  "duration_ms": 150.5,
  "error_type": "rate_limit|validation_error|server_error|authentication_error",
  "error_message": "Mensaje de error detallado",
  "status_code": 429,
  "resend_id": "resend_id_obtenido_de_resend",
  "environment": "production",
  "service_version": "1.0.0",
  "service_name": "amail"
}
```

### Eventos Registrados

| Evento | Descripción |
|--------|-------------|
| `email_send_start` | Inicio de intento de envío |
| `email_send_success` | Envío exitoso |
| `email_send_failure` | Envío fallido |
| `email_retry` | Reintento de envío |
| `email_send_with_retry_start` | Inicio de envío con reintentos |
| `email_send_with_retry_success` | Éxito después de reintentos |
| `email_send_with_retry_failure` | Fallo después de todos los reintentos |
| `email_health_check_failure` | Fallo en health check |

### Campos de Log

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `request_id` | string | UUID único por cada intento de envío |
| `timestamp` | ISO8601 | Timestamp UTC |
| `event` | string | Tipo de evento |
| `to` | string | Email del destinatario |
| `subject` | string | Asunto del email (truncado a 100 chars) |
| `duration_ms` | float | Duración en milisegundos |
| `error_type` | string | Tipo de error |
| `error_message` | string | Mensaje de error |
| `status_code` | int | Código HTTP de respuesta de Resend |
| `resend_id` | string | ID del email en Resend |

### Privacidad

**NO se loguea:**
- Contraseñas o tokens
- Contenido del cuerpo del email
- Datos personales sensibles

**SÍ se loguea:**
- Email del destinatario (necesario para debugging)
- Asunto (truncado a 100 caracteres)
- Metadatos de la operación

---

## Métricas Prometheus

### Métricas Disponibles

#### Contadores

```promql
# Intentos totales de envío
email_send_total{status="success|failure"}

# Fallos por tipo de error
email_send_failure_total{error_type="rate_limit|validation_error|server_error|authentication_error"}

# Reintentos
email_retry_total{attempt_number="2|3"}

# Health checks
email_health_check_total{status="healthy|unhealthy"}
```

#### Histogramas

```promql
# Latencia de envío (segundos)
email_send_duration_seconds_bucket
email_send_duration_seconds_sum
email_send_duration_seconds_count
```

#### Gauges

```promql
# Rate limit remaining
resend_rate_limit_remaining

# Rate limit reset timestamp
resend_rate_limit_reset
```

### Consultas Útiles

```promql
# Tasa de error (5 minutos)
sum(rate(email_send_total{status="failure"}[5m])) / sum(rate(email_send_total[5m])) * 100

# Latencia p50
histogram_quantile(0.50, sum(rate(email_send_duration_seconds_bucket[5m])) by (le)) * 1000

# Latencia p95
histogram_quantile(0.95, sum(rate(email_send_duration_seconds_bucket[5m])) by (le)) * 1000

# Latencia p99
histogram_quantile(0.99, sum(rate(email_send_duration_seconds_bucket[5m])) by (le)) * 1000

# Errores por tipo (última hora)
sum by (error_type) (increase(email_send_failure_total[1h]))
```

---

## Health Checks

### Endpoint Principal

```
GET /health
```

Respuesta:
```json
{
  "status": "healthy"
}
```

### Health Check de Email

```
GET /health/email
```

Envía un email de prueba a `test@resend.dev` y retorna:

```json
{
  "status": "healthy",
  "latency_ms": 150.5,
  "status_code": 200,
  "resend_id": "resend_xxx",
  "test_email": "test@resend.dev",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

En caso de fallo:
```json
{
  "status": "unhealthy",
  "latency_ms": 5000.0,
  "status_code": 429,
  "error": "Rate limit exceeded",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Uso en Kubernetes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/email
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 60
```

---

## Reintentos

### Configuración

- **Máximo de reintentos:** 3
- **Backoff exponencial:** 1s, 2s, 4s (multiplicador: 1, mínimo: 1s, máximo: 10s)

### Errores que se Reintentan

| Código | Tipo | Descripción |
|--------|------|-------------|
| 429 | `rate_limit` | Rate limit excedido |
| 500 | `server_error` | Error interno de Resend |
| 502 | `server_error` | Bad Gateway |
| 503 | `server_error` | Servicio no disponible |
| 504 | `server_error` | Timeout |

### Errores que NO se Reintentan

| Código | Tipo | Descripción |
|--------|------|-------------|
| 400 | `validation_error` | Email inválido o malformado |
| 401 | `authentication_error` | Error de autenticación |
| 403 | `forbidden` | Acceso denegado |
| 404 | `not_found` | Recurso no encontrado |

### Logs de Reintentos

Cada reintento genera un log:

```json
{
  "request_id": "uuid",
  "event": "email_retry",
  "attempt_number": 2,
  "max_attempts": 3,
  "to": "destinatario@ejemplo.com"
}
```

---

## Dashboards

### Grafana

Importar el dashboard desde `grafana/dashboards/email-dashboard.json`

#### Paneles Incluidos

1. **Error Rate (5m)** - Porcentaje de errores
2. **Latency (p50, p95, p99)** - Latencia de envío
3. **Rate Limit Remaining** - Cuota restante
4. **Emails Sent (1h)** - Total de envíos
5. **Failures by Type** - Fallos por tipo
6. **Service Health** - Estado del servicio

---

## Alertas

### Alertas Configuradas

| Alerta | Condición | Severidad |
|--------|-----------|-----------|
| `HighEmailErrorRate` | Error rate > 5% en 5min | Critical |
| `HighEmailLatencyP95` | p95 > 3s en 5min | Warning |
| `ResendRateLimitLow` | Rate limit < 100 | Warning |
| `EmailHealthCheckFailing` | Health check falla > 2min | Critical |
| `HighRetryRate` | Retry rate > 20% | Warning |
| `EmailServiceDown` | Servicio caido > 1min | Critical |

### Configuración de Notificaciones

Las alertas están configuradas en `alerts/email-alerts.yml` y requieren:
- Alertmanager configurado
- Canales de notificación (Slack, PagerDuty, Email, etc.)

---

## Consulta de Logs

### Buscar por Request ID

Para encontrar todos los logs asociados a un envío específico:

```
# Elasticsearch/Kibana
request_id: "550e8400-e29b-41d4-a716-446655440000"

# AWS CloudWatch Logs
fields @message | filter request_id = "550e8400-e29b-41d4-a716-446655440000"

# GCP Logging
resource.type="cloud_run_revision" AND jsonPayload.request_id="550e8400-e29b-41d4-a716-446655440000"
```

### Buscar Errores Recientes

```
# Todos los fallos en la última hora
event: "email_send_failure"

# Fallos de rate limit
error_type: "rate_limit"

# Errors con latencia alta
event: "email_send_failure" AND duration_ms > 5000
```

### Ejemplo de Traza Completa

```
# Inicio
{"request_id": "abc-123", "event": "email_send_start", "to": "user@example.com"}

# Reintento 1
{"request_id": "abc-123", "event": "email_retry", "attempt_number": 2}

# Reintento 2
{"request_id": "abc-123", "event": "email_retry", "attempt_number": 3}

# Éxito
{"request_id": "abc-123", "event": "email_send_success", "resend_id": "resend_xyz", "duration_ms": 200}
```

---

## Configuración de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno (dev/staging/prod) | `development` |
| `VERSION` | Versión del servicio | `1.0.0` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

---

## Archivos de Configuración

- `app/logging_config.py` - Configuración de logging
- `app/metrics.py` - Definición de métricas
- `app/providers/resend/sender.py` - Lógica de envío con logging
- `prometheus/prometheus.yml` - Configuración de Prometheus
- `grafana/dashboards/email-dashboard.json` - Dashboard
- `alerts/email-alerts.yml` - Definición de alertas
