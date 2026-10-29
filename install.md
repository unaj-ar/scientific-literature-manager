2. Clonar el repositorio e instalar dependencias# Crear y activar entorno virtual
python -m venv venv

# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate

# Instalar librerías
pip install -r requirements.txt
3. Configurar Variables de Entorno (.env)Crea un archivo .env en la raíz del proyecto con las credenciales de tu base de datos:DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_NAME=academic_management
💻 Modos de UsoOpción A: Interfaz Web + API REST (Recomendado)Iniciar el servidor API con Uvicorn:uvicorn api:app --reload
Abrir la aplicación en el navegador:
Ingresa a http://127.0.0.1:8000 para acceder a la plataforma web.Documentación Swagger interactiva:
Puedes explorar y probar los endpoints directamente en http://127.0.0.1:8000/docs.Opción B: Consola de Comandos (CLI)Si prefieres trabajar directamente desde la terminal:python main.py
📡 Endpoints de la API RESTMétodoEndpointDescripciónGET/Carga la interfaz Web (index.html)GET/articlesObtiene la lista general de artículos ordenada por prioridad (P1 > P2 > P3)GET/articles/author/{name}Consulta todos los artículos asociados a un autor específicoPOST/articlesRegistra un nuevo artículo y vincula automáticamente sus autores