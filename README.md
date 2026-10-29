<<<<<<< HEAD
# scientific-literature-manager
revisión sistematica de la literatura

correr con uvicorn api:app --reload
=======
# 📚 Scientific Literature Manager

Un sistema integral diseñado para organizar y optimizar el ciclo de vida de la investigación científica: **Descubrimiento**, **Organización**, **Priorización** y **Recuperación** de artículos académicos.

El proyecto cuenta con una arquitectura en capas en **Python**, persistencia en **PostgreSQL** con modelo relacional Normalizado (3NF), una API REST con **FastAPI** y una interfaz web interactiva.

---

## 🏛️ Arquitectura del Proyecto

El código está estructurado siguiendo el principio de **Separación de Responsabilidades (SoC)**:

```text
scientific_literature_manager/
├── config/                  # Gestión de conexiones (PostgreSQL)
│   └── database.py
├── repository/              # Capa de acceso a datos (Consultas SQL)
│   └── article_repository.py
├── services/                # Lógica de negocio y validaciones
│   └── literature_service.py
├── ui/                      # Interfaz de Consola (CLI)
│   └── cli.py
├── .env                     # Variables de entorno (No subir a Git)
├── api.py                   # Servidor API REST (FastAPI)
├── index.html               # Frontend Web
├── main.py                  # Punto de entrada para la consola CLI
└── requirements.txt         # Dependencias del proyecto


 uvicorn api:app --reload
