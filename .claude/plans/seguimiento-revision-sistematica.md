# Plan — Seguimiento de la revisión sistemática y generación de índice

| | |
|---|---|
| Estado | Propuesto, sin implementar |
| Fecha | 2026-11-10 |
| Base | Rama `agent` (roles, permisos y consola admin ya implementados) |
| Relacionado | [documento-funcional.md](../docs/documento-funcional.md), [PLAN_CORRECCIONES.md](PLAN_CORRECCIONES.md) |

---

## 1. Objetivo

Que cada investigador pueda **llevar su propia revisión sistemática**: marcar qué artículos le interesan, cuáles está siguiendo para escribir su paper, cuáles descarta y por qué, y **generar automáticamente un índice** a partir de lo que reunió.

Hoy los artículos son un catálogo **global**: no hay forma de saber qué le importa a cada usuario. Este plan agrega una capa **por usuario** encima del catálogo, sin cambiar el catálogo.

## 2. Alcance

**Incluye**
- Revisiones (una por paper) con título, pregunta de investigación y estado.
- Seguimiento por usuario y revisión de cada artículo: estado, interés, notas propias y sección del paper.
- Temas/secciones propias para organizar los artículos.
- Índice automático del paper y de las referencias, exportable.
- Pantalla web para trabajar la revisión.

**No incluye (primera versión)**
- Importar desde bases bibliográficas (Scopus, PubMed, etc.).
- Edición colaborativa de una revisión entre varios usuarios.
- Redacción del texto del paper ni resúmenes con IA.
- Diagrama PRISMA completo (se deja el conteo básico).

## 3. Decisiones pendientes (confirmar antes de implementar)

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| D1 | ¿Qué es el "índice automático"? | **Ambos**: (a) índice del paper (secciones con sus artículos) y (b) índice de referencias (por autor y año). Se genera desde lo que el usuario siguió |
| D2 | ¿Un usuario puede tener varias revisiones? | Sí (una por paper) |
| D3 | ¿Los artículos nuevos los ve todo el mundo o son privados del usuario? | El catálogo sigue siendo **global**; lo privado es el seguimiento |
| D4 | ¿Cómo se arma la estructura del paper? | El usuario define secciones; el sistema **sugiere** una agrupación inicial según etiquetas (`tags`) |
| D5 | ¿Formatos de exportación? | Markdown primero; BibTeX después |
| D6 | ¿El admin puede ver las revisiones de otros? | No en v1 (privacidad); solo conteos agregados |
| D7 | ¿Se usa IA para sugerir secciones? | No en v1; el agrupamiento es determinista (etiquetas, año, autores) |
| D8 | ¿Dónde se guarda el abstract? | En `articles.abstract` (catálogo global, columna ya existente); las notas propias van en `review_articles.personal_notes` (ver 5.1) |
| D9 | ¿Quién puede corregir un abstract? | Administradores; quien dio de alta el artículo cuando exista `created_by` |
| D10 | ¿Con qué identificador se busca y gestiona desde afuera? | **UUID** público en rutas, respuestas y token; el `id` entero queda solo como clave interna (ver 5.0) |

## 4. Conceptos y vocabulario

- **Revisión** (`review`): el trabajo de un usuario para un paper.
- **Seguimiento** (`review_article`): la relación de un artículo con una revisión, con su estado y notas.
- **Sección** (`review_section`): capítulo o tema del paper; se ordena y puede anidarse un nivel.
- **Índice**: documento generado con las secciones y los artículos asignados a cada una.

### Estados de un artículo dentro de una revisión

```text
candidate  →  following  →  included
    │             │
    └──→ excluded ←┘
```

| Estado | Significado |
|---|---|
| `candidate` | Lo encontré; falta decidir |
| `following` | Me interesa; lo estoy leyendo o lo voy a usar |
| `included` | Entra en el paper (se cita) |
| `excluded` | Descartado; **requiere motivo** |

El estado de lectura que ya existe en el artículo (`Unread`, `In Progress`, `Read`, `Archived`) es global y no se toca. Este estado es la **decisión del usuario sobre esa revisión**.

## 5. Modelo de datos

### 5.0 Identificadores públicos: UUID (script `scripts/V005.sql`, Fase 0)

**Decisión (D10):** todo recurso expuesto se identifica por un `uuid`. El `id` entero (`SERIAL`) se mantiene como clave primaria **interna** para claves foráneas y `JOIN`, y **nunca** aparece en rutas, respuestas, token ni pantallas.

Por qué:
- Los ids secuenciales se pueden recorrer (`/users/1`, `/users/2`, …) y revelan cuántos registros hay y su orden de creación.
- El UUID no cambia aunque se migre o se fusione la base.
- Cambiar las claves primarias obligaría a reescribir todas las tablas y relaciones sin ganancia real; una columna adicional da la ventaja sin ese riesgo.

Aclaración: el UUID **no reemplaza la autorización**. Los chequeos de permiso y de dueño (sección 7) siguen siendo obligatorios.

Cambios en la base (idempotentes):
- `ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid UUID NOT NULL DEFAULT gen_random_uuid();` y lo mismo en `articles`. Las filas existentes reciben su UUID al agregar la columna.
- Restricción `UNIQUE` (índice) sobre cada `uuid`, creada con `IF NOT EXISTS`.
- `gen_random_uuid()` es nativa desde PostgreSQL 13; el proyecto exige 14 o superior, así que no hace falta ninguna extensión.
- `authors` y `article_authors` no se exponen, por lo que **no** llevan UUID por ahora.
- Las tablas nuevas (`reviews`, `review_sections`) ya nacen con su `uuid` (`V006.sql`).

Cambios en el código:
- **Rutas:** `/users/{uuid}`, `/articles/{uuid}`, `/reviews/{uuid}`; el parámetro se declara como `uuid.UUID`, así un valor mal formado devuelve 422 sin llegar a la base.
- **Repositorios:** métodos `get_by_uuid`, y las operaciones de la API reciben UUID; internamente se resuelve al `id` entero una sola vez y los `JOIN` siguen usándolo.
- **Respuestas:** el campo `id` se reemplaza por `uuid` (en `/users`, `/articles`, `/me`, `/register`, `/login`).
- **Token JWT:** el claim `user_id` pasa a llevar el UUID del usuario. Las sesiones vigentes dejan de ser válidas y hay que volver a iniciar sesión (se avisa en el PR).
- **Servicios:** las reglas (auto-baja, último admin, cambio de rol) comparan UUID, no enteros.
- **UI y CLI:** `admin.html`, `index.html` y la CLI usan el UUID (la CLI puede mostrar una versión corta de 8 caracteres).
- **Tests:** `FakeUserRepo` genera UUID; casos nuevos de UUID inválido (422) y de UUID inexistente (404).

Orden: esta fase va **antes** de revisiones, como un PR propio, para que todo lo nuevo nazca con UUID.

### 5.1 Modelo de las revisiones (script `scripts/V006.sql`, idempotente)

```text
reviews
  id, uuid, user_id → users, title, research_question, status (draft|in_progress|completed),
  created_at, updated_at, is_active, deleted_at

review_sections
  id, uuid, review_id → reviews, parent_id → review_sections (nullable), title, position

review_articles
  review_id → reviews, article_id → articles          (clave compuesta)
  decision (candidate|following|included|excluded)  DEFAULT candidate
  interest (1–5, nullable)
  exclusion_reason (texto; obligatorio si excluded)
  personal_notes, section_id → review_sections (nullable)
  added_at, updated_at
```

Notas:
- `CHECK` en `decision`, `interest` y `status` (como en `users.role`).
- Índices: `reviews(user_id)`, `review_articles(review_id, decision)`, `review_sections(review_id, position)`.
- `ON DELETE CASCADE` desde `reviews` hacia secciones y seguimientos; el catálogo `articles` nunca se borra por una revisión.
- Baja lógica en `reviews` (mismo patrón `is_active` + `deleted_at`).
- Los scripts `V002`–`V005` se aplican antes; **no** editar los ya existentes.
- `review_articles` usa los `id` internos como clave compuesta; hacia afuera, la API siempre expone los UUID.

### 5.2 Dónde se guarda el abstract de cada paper

**Decisión: en el catálogo global, en la columna que ya existe `articles.abstract` (`TEXT`).** No se crea una columna ni una tabla nueva.

| Dato | Dónde vive | Quién lo ve | Para qué |
|---|---|---|---|
| **Abstract original** del paper | `articles.abstract` | Todos los usuarios con `articles:read` | Texto oficial del paper; es el mismo para todos |
| Notas y resumen **propios** | `review_articles.personal_notes` | Solo el dueño de la revisión | Lo que el usuario entendió y cómo lo usará |
| Notas iniciales del alta | `articles.notes` (ya existe) | Todos | Comentario general al registrar; no se usa para el abstract |

Por qué en `articles` y no por revisión:
- El abstract es un dato del paper, no una opinión del usuario: no se duplica si dos usuarios siguen el mismo artículo.
- La columna `abstract` ya está en `V002.sql`, así que **no hace falta migración** para guardarlo. Solo falta usarla.

Estado actual (verificado en el código): la columna existe pero **ningún código la lee ni la escribe**. `ArticleSchema` (API), `ArticleRepository.create_article`, `LiteratureService.register_new_article` y los formularios no la contemplan. Lo que hoy se guarda como "resumen" va a `notes`.

Trabajo necesario (Fase 1):
1. `ArticleSchema` y `register_new_article`: nuevo campo opcional `abstract`.
2. `ArticleRepository.create_article`: incluir `abstract` en el `INSERT`.
3. Consultas `get_by_priority` y `get_by_author`: devolver `abstract` (en el listado general conviene recortarlo o pedirlo por detalle, para no inflar la respuesta).
4. Nuevo `GET /articles/{uuid}` con el detalle completo, incluido el abstract.
5. Formulario de alta en `ui/index.html` y en la CLI: campo "Abstract" (área de texto).
6. Mostrarlo en el panel de detalle de `reviews.html`, junto a las notas personales (el original arriba y las notas propias debajo, bien diferenciados).

Reglas:
- Texto plano, hasta 10 000 caracteres (validado en la API; `TEXT` no lo limita). Vacío se guarda como nulo.
- Se muestra siempre con `textContent` (nunca `innerHTML`), porque es texto pegado de fuentes externas.
- Si el abstract se carga mal, lo corrige quien dio de alta el artículo o un administrador (requiere `created_by`, ver sección 14; hasta entonces, solo administradores).
- El índice generado puede incluir el abstract de cada artículo con `?include_abstract=true` (por defecto no, para que el índice sea corto).
- Búsqueda: en una segunda etapa se puede agregar búsqueda de texto completo sobre `title` y `abstract` (`tsvector` con índice GIN) para encontrar artículos por contenido.

## 6. Reglas de negocio

| # | Regla |
|---|---|
| RR-01 | Una revisión pertenece a un usuario; solo ese usuario la ve y la modifica |
| RR-02 | Un artículo aparece una sola vez por revisión |
| RR-03 | Excluir requiere `exclusion_reason` no vacío |
| RR-04 | `interest` va de 1 a 5 |
| RR-05 | Solo se asigna a una sección que pertenezca a la misma revisión |
| RR-06 | Un artículo `excluded` no puede tener sección ni aparecer en el índice |
| RR-07 | Borrar una sección deja sus artículos sin sección (no los borra) |
| RR-08 | Se puede mover una sección solo dentro de su revisión; el anidado es de un nivel |
| RR-09 | Dar de baja a un usuario oculta sus revisiones pero no las borra |

## 7. Permisos

Nuevos permisos en `services/permissions.py`, para ambos roles:

| Permiso | `researcher` | `admin` |
|---|:---:|:---:|
| `reviews:read` (las propias) | ✔ | ✔ |
| `reviews:write` (las propias) | ✔ | ✔ |

La pertenencia se valida en el servicio (`review.user_id == usuario`), no solo con el permiso: un permiso correcto sobre una revisión ajena devuelve **404** (no 403, para no revelar que existe).

## 8. API

| Método y ruta | Descripción |
|---|---|
| `POST /reviews` · `GET /reviews` | Crear y listar mis revisiones |
| `GET/PATCH/DELETE /reviews/{uuid}` | Ver, editar y dar de baja |
| `GET /reviews/{uuid}/articles?decision=&section=&q=` | Artículos de la revisión, con filtros |
| `PUT /reviews/{uuid}/articles/{article_uuid}` | Agregar o actualizar seguimiento (decisión, interés, notas, sección) |
| `DELETE /reviews/{uuid}/articles/{article_uuid}` | Quitar de la revisión |
| `POST/PATCH/DELETE /reviews/{uuid}/sections` (cada sección tiene su propio `uuid`) | Gestionar secciones y su orden |
| `POST /reviews/{uuid}/sections/suggest` | Proponer secciones desde las etiquetas de los artículos seguidos (no guarda hasta confirmar) |
| `GET /reviews/{uuid}/summary` | Conteos por decisión y por sección |
| `GET /reviews/{uuid}/index?format=json\|md&include_abstract=` | Índice del paper y referencias (el abstract es opcional) |
| `GET /articles/{uuid}` | Detalle de un artículo, con su abstract (nuevo, ver 5.2) |
| `PATCH /articles/{uuid}/abstract` | Corregir el abstract (administradores) |

Errores: 404 revisión ajena o inexistente, 409 artículo repetido, 422 UUID mal formado o reglas RR-03/04/05.

Endpoints existentes que cambian con la Fase 0: `DELETE /users/{uuid}`, `PATCH /users/{uuid}/restore` y `PATCH /users/{uuid}/role`. Los listados (`GET /users`, `GET /articles`) devuelven `uuid` en lugar de `id`.

## 9. Índice automático

### 9.1 Contenido

1. **Índice del paper**: secciones en orden, con los artículos `following` e `included` de cada una.
2. **Sin sección**: artículos seguidos que todavía no se asignaron (se listan aparte para completar).
3. **Índice de referencias**: lista ordenada por autor y año (solo `included`).
4. **Resumen**: totales por decisión y artículos excluidos con su motivo (útil para la sección de metodología).

### 9.2 Algoritmo (determinista, sin IA)

1. Tomar los artículos de la revisión con decisión `following` o `included`.
2. Agrupar por `section_id`; ordenar secciones por `position`.
3. Dentro de cada sección: `included` primero, luego por interés descendente, luego por año.
4. Referencias: ordenar por primer autor, año y título; numerar.
5. Si la revisión no tiene secciones, proponerlas por **etiquetas** (`tags`): una sección por etiqueta frecuente, el resto en "Otros".

### 9.3 Formato de salida (Markdown)

```markdown
# <Título de la revisión>
_Pregunta de investigación: …_

## 1. <Sección>
- [1] Autor, A.; Autor, B. (2023). *Título.* DOI — Interés 5 ★ — incluido
…

## Referencias
1. Autor, A.; Autor, B. (2023). Título. DOI
```

BibTeX queda para una segunda etapa (D5).

## 10. Interfaz web

Nueva pantalla `ui/reviews.html` (enlace desde `index.html`):

- **Lista de revisiones** con crear, abrir y dar de baja.
- **Vista de revisión** en tres paneles: secciones (izquierda), artículos filtrables por decisión e interés (centro) y detalle con notas (derecha).
- **Acciones rápidas** sobre un artículo: seguir, incluir, excluir (pide motivo), puntuar, asignar sección.
- **Botón "Generar índice"**: vista previa y descarga `.md`.
- En el listado general de `index.html`, botón "Agregar a mi revisión" por artículo.

Respetar lo ya hecho en `ui/`: token en `localStorage`, redirección a login ante 401 y texto del usuario siempre con `textContent` (nunca `innerHTML`) para evitar XSS.

## 11. Cambios por capa

| Capa | Archivos nuevos o modificados |
|---|---|
| SQL | `scripts/V005.sql` (UUID, Fase 0) y `scripts/V006.sql` (revisiones) |
| Repositorio | `repository/review_repository.py` (interfaces pequeñas, separadas para revisiones, seguimiento y secciones); `repository/article_repository.py` para leer y escribir `abstract` |
| Servicios | `services/review_service.py`, `services/review_index_service.py` (generación del índice, sin SQL ni HTTP) |
| API | `routers/reviews.py` (primer router; `api.py` lo incluye) y esquemas Pydantic |
| Permisos | `services/permissions.py` |
| UUID (Fase 0) | `api.py`, `repository/user_repository.py`, `repository/article_repository.py`, `services/user_service.py`, `services/auth_service.py` (claim del token), `ui/admin.html`, `ui/index.html`, `ui/cli.py`, `tests/` |
| UI | `ui/reviews.html`, enlaces en `ui/index.html` |
| Docs | Actualizar `documento-funcional.md` y `AGENTS.md` (estructura) |

Diseño: los servicios reciben el repositorio por constructor y no lanzan `HTTPException`; usan excepciones de negocio que `api.py` traduce (alineado con la auditoría SOLID). `ReviewIndexService` es una función pura sobre datos ya cargados, lo que facilita probarla.

## 12. Tests

| Qué | Cómo |
|---|---|
| Reglas RR-01 a RR-09 | Tests de servicio con repositorio simulado |
| Generación del índice | Tests puros: orden de secciones, artículos sin sección, excluidos fuera, referencias ordenadas, revisión vacía |
| Aislamiento entre usuarios | API con `TestClient` y `FakeReviewRepo`: otro usuario recibe 404 |
| Permisos | Sin token 401; investigador y admin acceden solo a las suyas |
| Migración | Verificar `V005.sql` y `V006.sql` dos veces seguidas contra una base de prueba (idempotencia); las filas existentes quedan con UUID único y no nulo |
| UUID | Rutas con UUID válido, mal formado (422) e inexistente (404); ninguna respuesta incluye el `id` entero; el token lleva el UUID; un token con el formato anterior se rechaza (401) |
| Exportación | Comparar el Markdown generado contra un archivo de referencia |
| Abstract | Alta con y sin abstract (vacío → nulo); límite de 10 000 caracteres (422); aparece en el detalle y en el índice solo con `include_abstract`; el contenido con HTML se devuelve como texto, sin interpretarse |

Meta: cobertura del 80 % o más en los módulos nuevos.

## 13. Fases y orden de PRs

| Fase | Entrega | PR sugerido |
|---|---|---|
| 0 | **UUID públicos**: `V005.sql`, rutas, respuestas, token, UI, CLI y tests (5.0) | `feat: Use UUID as public identifier` |
| 1 | `V006.sql`, repositorio y servicio de revisiones y seguimiento, API de revisiones y artículos, **soporte del abstract en alta y detalle (5.2)**, tests | `feat: Add reviews and article tracking` |
| 2 | Secciones, asignación y sugerencia por etiquetas | `feat: Add review sections` |
| 3 | Índice automático (JSON y Markdown) y resumen | `feat: Add automatic review index` |
| 4 | Pantalla `reviews.html` y botón en `index.html` | `feat: Add reviews web screen` |
| 5 | Exportación BibTeX y mejoras (opcional) | `feat: Add BibTeX export` |

Cada fase deja la app funcionando y mergeable. Orden de merge: SQL → API → UI.

## 14. Riesgos

| Riesgo | Mitigación |
|---|---|
| Artículos globales: otro usuario podría ver notas ajenas | Las notas y decisiones viven solo en `review_articles`, nunca en `articles` |
| El catálogo no distingue quién cargó cada artículo | Agregar `created_by` a `articles` (opcional, fase 1 o 2) para filtrar "mis artículos" |
| Etiquetas libres y sucias generan secciones pobres | Normalizar (minúsculas, espacios) y dejar el resultado como **sugerencia** editable |
| Revisiones grandes (cientos de artículos) | Paginación y filtros en el listado; índices SQL |
| `ArticleRepository` abre su propia conexión | Para consultas que cruzan `articles` y `review_articles`, el repositorio nuevo usa la misma conexión inyectada |
| El cambio a UUID invalida las sesiones y rompe clientes que usen ids enteros | PR propio y primero; avisar que hay que volver a iniciar sesión; no hay más clientes que la UI y la CLI |
| Tratar el UUID como secreto | Es un identificador, no una credencial: permisos y dueño se validan siempre |
| Trabajo por hacer en el plan de correcciones (seguridad, `SECRET_KEY`, CORS) | Resolver la Fase 2 de seguridad antes de exponer datos privados por usuario |

## 15. Definición de terminado

- [ ] `V005.sql` y `V006.sql` aplicados dos veces sin error; usuarios y artículos existentes con UUID.
- [ ] Ninguna ruta ni respuesta expone el `id` entero.
- [ ] Un investigador crea una revisión, marca artículos como seguidos, incluidos o excluidos (con motivo) y los organiza en secciones.
- [ ] Otro usuario no puede ver ni modificar esa revisión.
- [ ] `GET /reviews/{uuid}/index?format=md` devuelve el índice correcto.
- [ ] El abstract se carga en el alta, se guarda en `articles.abstract` y se ve en el detalle del artículo.
- [ ] Pantalla web operativa con descarga del índice.
- [ ] `pytest` y `ruff check .` en verde; documento funcional y `AGENTS.md` actualizados.
