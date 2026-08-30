# TODO

Tareas pendientes del proyecto Amail.

## Authentication

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
