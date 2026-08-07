# TODO

Tareas pendientes del proyecto Amail.

## Autenticacion

- [ ] Definir el esquema de autenticacion (API key vs JWT vs OAuth).
- [ ] Proteger los endpoints de envio (`POST /api/v1/send`, `POST /api/v1/send/batch`).
- [ ] Decidir que rutas quedan publicas (`/health*`, `/api/v1/templates`) y cuales requieren auth.
- [ ] Implementar el mecanismo: verificacion del token/header, dependencia FastAPI de auth.
- [ ] Gestion de credenciales (rotacion, almacen seguro via env/secret manager).
- [ ] Tests de auth: 401 sin credenciales, 403 con token invalido, happy path.

## Rate limiting

- [ ] Elegir estrategia (por IP vs por API key; ventana fija vs sliding window).
- [ ] Seleccionar libreria / mecanismo (p. ej. slowapi, o middleware propio).
- [ ] Definir limites por endpoint (send, batch, webhook) y por cliente.
- [ ] Devolver headers estandar `RateLimit-Limit` / `RateLimit-Remaining` / `Retry-After`.
- [ ] Manejar respuestas 429 con el cuerpo de error tipado (`ErrorDetail`).
- [ ] Tests de rate limit: exceder limite -> 429, respeto de ventana, headers presentes.

## Preview de plantillas (Email Client Preview)

Frontend sencillo para visualizar como se verian las plantillas de correo en los principales servicios de email.

- [ ] Crear un frontend ligero (page/route) que renderice una plantilla de correo.
- [ ] Soportar preview simulando los estilos de 3 servicios de email (p. ej. Gmail, Outlook, Apple Mail), copiando sus estilos.
- [ ] Permitir seleccionar la plantilla a previsualizar (via `GET /api/v1/templates`).
- [ ] Exponer el preview como un endpoint/configuracion de la API para poder bloquearlo en produccion.
- [ ] Bloquear/gating del cliente de preview en entornos productivos (feature flag o config).
- [ ] Tests del endpoint de preview.
