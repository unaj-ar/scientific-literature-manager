---
name: python-revision-write-tests
description: Write unit tests (service layer) and pure unit controller/API tests (no app context or DB connections) for pythonRevisionRepositoryProject following project conventions and test-speed rules. Use when asked to write, add, or improve tests for a service, repository, or controller in this repo, including reaching ≥80% coverage on existing test files.
---

# pythonRevisionRepositoryProject — Write Tests

Guía para escribir tests de **service/domain (unit)** y **controllers/routers (unit puro, sin levantar servidor HTTP ni base de datos)** siguiendo los patrones activos de `pythonRevisionRepositoryProject`.
Aplica tanto para crear tests desde cero como para **completar coverage en tests existentes hasta ≥ 80%**.

---

## Regla de velocidad (leer primero)

La suite de tests debe ejecutarse en milisegundos. Para evitar ralentizaciones causadas por la inicialización de la aplicación, clientes HTTP (`TestClient`) o conexiones a bases de datos:

| Capa | Archivo / Módulo | Cómo | Contexto pesado |
|---|---|---|---|
| Unit (Services / Domain) | `test_xxx_service.py` | `pytest` + `unittest.mock` (`MagicMock` / `mocker`) | No |
| Unit puro (Controllers / Routers) | `test_xxx_controller.py` | Invocación directa a métodos/funciones inyectando mocks de services | No |
| Smoke / Integración | `test_xxx_integration.py` | Base de datos de test (`SQLite` en memoria / DB de test) | Sí, aislado |

- **Nunca** instanciar la aplicación completa ni usar `TestClient` en tests unitarios de controllers o services salvo que se pruebe explícitamente la pila de middleware.
- **Nunca** ejecutar consultas a la base de datos real en tests etiquetados como `@pytest.mark.unit`.
- El contexto de base de datos solo se justifica en la [Capa 3](#capa-3--smoke--integración-contexto-de-base-de-datos).

---

## Modo 1 — Tests desde cero

Ir directamente a [Capa 1](#capa-1--unit-test-service--domain) y [Capa 2](#capa-2--controller--router-test-unit-puro).

## Modo 2 — Completar coverage en tests existentes

Seguir este flujo antes de escribir cualquier test nuevo:

### Paso A — Medir el coverage actual

```bash
# Generar reporte de coverage en consola y en HTML
pytest --cov=pythonRevisionRepositoryProject --cov-report=term-missing --cov-report=html tests/unit/test_xxx_service.py tests/unit/test_xxx_controller.py

# Resumen rápido en consola
coverage report -m | grep "xxx"