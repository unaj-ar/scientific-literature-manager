# Documento funcional — Scientific Literature Manager

| | |
|---|---|
| Versión | 1.0 (borrador) |
| Fecha | 2026-11-10 |
| Estado | Describe el comportamiento **implementado** en la rama `agent` (incluye el trabajo de roles y consola admin). Lo pendiente está en la sección 9. |
| Fuente | Código del repo (`api.py`, `services/`, `repository/`, `scripts/`, `ui/`). Si algo no coincide con el negocio, corregir este documento o el código, no ambos por separado. |

---

## 1. Propósito

Ayudar a investigadores a gestionar la literatura científica de una revisión sistemática: **descubrir** artículos (alta), **organizarlos** (autores, etiquetas, PDF, notas), **priorizarlos** (P1–P3 y estado de lectura) y **recuperarlos** (listado priorizado y búsqueda por autor).

## 2. Alcance

**Incluye:** gestión de artículos y autores, autenticación, roles y permisos, administración de usuarios (consola web), interfaz web y CLI.

**No incluye (hoy):** edición o baja de artículos, carga de archivos PDF (solo se guarda una ruta o enlace), importación desde bases bibliográficas, recuperación de contraseña, verificación de email, notificaciones.

## 3. Actores y roles

| Actor | Rol en el sistema | Qué puede hacer |
|---|---|---|
| Visitante | — | Registrarse e iniciar sesión |
| Investigador | `researcher` | Ver y crear artículos, buscar por autor |
| Administrador | `admin` | Todo lo del investigador, más gestionar usuarios |

### Permisos

| Permiso | Investigador | Administrador |
|---|:---:|:---:|
| `articles:read` | ✔ | ✔ |
| `articles:create` | ✔ | ✔ |
| `users:manage` | — | ✔ |

El permiso se valida contra la base de datos **en cada petición**: una baja o un cambio de rol rige de inmediato, aunque el usuario conserve un token vigente.

## 4. Requerimientos funcionales

### 4.1 Cuentas y sesión
- **RF-01 Auto-registro.** Cualquier visitante puede crear una cuenta con usuario (3–50 caracteres), email válido y contraseña (8–128 caracteres). La cuenta siempre se crea como `researcher`, aunque la petición pida otro rol.
- **RF-02 Inicio de sesión.** Con usuario y contraseña se obtiene un token JWT (vigencia 60 minutos) y el rol. El mensaje de error es el mismo si el usuario no existe, está dado de baja o la contraseña es incorrecta.
- **RF-03 Perfil.** `GET /me` devuelve id, usuario, rol y permisos del usuario autenticado.
- **RF-04 Cierre de sesión.** Se descarta el token en el navegador (no hay revocación en el servidor; el token expira solo).
- **RF-05 Contraseñas.** Solo se guarda el hash (Argon2); nunca la contraseña.

### 4.2 Artículos
- **RF-10 Alta.** Un usuario con `articles:create` registra un artículo con: título (obligatorio), autores separados por coma (obligatorio), año, DOI, prioridad, estado, etiquetas, ruta o enlace al PDF y notas.
- **RF-11 Autores normalizados.** Cada autor es único en la tabla de autores (comparación sin distinguir mayúsculas). Un autor puede estar en varios artículos y un artículo tiene varios autores (N:M).
- **RF-12 Listado priorizado.** Un usuario con `articles:read` ve todos los artículos ordenados por prioridad (P1 primero) y, dentro de cada una, del más reciente al más antiguo, con sus autores concatenados.
- **RF-13 Búsqueda por autor.** Búsqueda parcial y sin distinguir mayúsculas por nombre de autor; resultados ordenados por año descendente. Un nombre vacío devuelve lista vacía.

### 4.3 Administración de usuarios (solo `users:manage`)
- **RF-20 Listar** todos los usuarios, incluidos los dados de baja.
- **RF-21 Crear** un usuario eligiendo su rol.
- **RF-22 Cambiar el rol** de otro usuario.
- **RF-23 Baja lógica.** El usuario queda inactivo (`is_active = false`, con fecha de baja); no se borra. No puede iniciar sesión ni usar su token.
- **RF-24 Reactivar** un usuario dado de baja.

## 5. Reglas de negocio

| # | Regla |
|---|---|
| RN-01 | El título no puede estar vacío. |
| RN-02 | Prioridad válida: `P1` (alta), `P2` (media), `P3` (baja). Cualquier otro valor se normaliza a `P2`. |
| RN-03 | Estado válido: `Unread`, `In Progress`, `Read`, `Archived`. El texto se normaliza sin distinguir mayúsculas (se acepta también `in progres`). Cualquier otro valor se normaliza a `Unread`. |
| RN-04 | El año debe ser numérico; si no lo es, se guarda vacío. |
| RN-05 | El DOI vacío se guarda como nulo. El DOI es único: repetirlo hace fallar el alta. |
| RN-06 | Los autores se separan por coma; se ignoran espacios y entradas vacías. |
| RN-07 | Usuario y email son únicos; repetirlos devuelve conflicto (409). |
| RN-08 | Un administrador no puede cambiar su propio rol ni darse de baja. |
| RN-09 | No se puede degradar ni dar de baja al **último administrador activo**. |
| RN-10 | Solo un administrador puede crear administradores; el auto-registro nunca los crea. |

## 6. Modelo de datos

| Tabla | Campos principales |
|---|---|
| `articles` | id, title, publication_year, doi (único), abstract, priority, status, tags, pdf_path, notes, created_at, is_active, deleted_at |
| `authors` | id, name (único) |
| `article_authors` | article_id, author_id (clave compuesta; borrado en cascada) |
| `users` | id, username (único), email (único), hashed_password, role (`admin`/`researcher`), is_active, deleted_at, created_at |

Scripts de base de datos, en orden: `V002.sql` (artículos y autores), `V003.sql` (usuarios y baja lógica), `V004.sql` (roles). `V001.sql` es una versión anterior del esquema y no debe aplicarse.

## 7. Interfaz

### 7.1 API REST
| Método y ruta | Permiso | Descripción |
|---|---|---|
| `POST /register` | público | Auto-registro (investigador) |
| `POST /login` | público | Token JWT y rol (formulario `username` y `password`) |
| `GET /me` | `articles:read` | Perfil y permisos |
| `GET /articles` | `articles:read` | Listado priorizado |
| `GET /articles/author/{nombre}` | `articles:read` | Búsqueda por autor |
| `POST /articles` | `articles:create` | Alta de artículo |
| `GET /users` | `users:manage` | Listar usuarios |
| `POST /users` | `users:manage` | Crear usuario con rol |
| `PATCH /users/{id}/role` | `users:manage` | Cambiar rol |
| `DELETE /users/{id}` | `users:manage` | Baja lógica |
| `PATCH /users/{id}/restore` | `users:manage` | Reactivar |

Códigos comunes: 401 (sin token, token inválido o usuario inactivo), 403 (sin permiso), 404 (usuario inexistente), 409 (duplicado), 422 (datos inválidos).

### 7.2 Pantallas web
| Pantalla | Ruta | Descripción |
|---|---|---|
| Inicio de sesión | `/` o `/login.html` | Redirige a la consola si el rol es admin, o a la lista de artículos si es investigador |
| Artículos | `/index.html` | Listado priorizado, búsqueda por autor y formulario de alta; enlace a la consola solo para admins |
| Consola de administración | `/admin.html` | Tabla de usuarios, alta con rol, cambio de rol, baja y reactivación |

### 7.3 Consola de comandos (CLI)
`python main.py`: menú para agregar artículo, ver la lista priorizada y buscar por autor. **No usa autenticación** (accede directo a la base).

### 7.4 Alta del primer administrador
`python -m scripts.create_admin --username <usuario> --email <email>`: crea el usuario con rol `admin` (pide la contraseña por consola) o promueve uno existente.

## 8. Flujos principales

1. **Primer uso:** aplicar `V002`–`V004` → crear administrador con el script → el admin inicia sesión y crea usuarios (o los investigadores se auto-registran).
2. **Investigador:** inicia sesión → ve la lista priorizada → agrega artículos → busca por autor.
3. **Baja de un usuario:** el admin pulsa "Dar de baja" → el usuario deja de poder operar de inmediato → el admin puede reactivarlo.

## 9. Restricciones y pendientes conocidos

- `SECRET_KEY` tiene un valor por defecto fijo; debe definirse por entorno antes de producción.
- CORS está abierto a cualquier origen.
- El error de un alta de artículo devuelve el mensaje interno de la base al cliente.
- Los artículos son globales (no pertenecen a un usuario) y no se pueden editar ni dar de baja; la columna `is_active` de `articles` existe pero no se usa.
- No hay límite de intentos de inicio de sesión ni revocación de tokens.
- La CLI no respeta roles ni permisos.
- Ver el plan de correcciones en `.claude/plans/PLAN_CORRECCIONES.md`.
