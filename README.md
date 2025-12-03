## Gestor de tareas - Esqueleto Flask

Aplicación mínima con Flask para que puedas empezar un proyecto rápidamente.

### Requisitos

- Python 3.10+ recomendado

Instala las dependencias:

```bash
pip install -r requirements.txt
```

### Ejecutar en desarrollo

Opción 1 (directo con Python):

```bash
python app.py
```

Opción 2 (usando Flask):

```bash
set FLASK_APP=app:create_app
set FLASK_ENV=development
flask run
```

En Linux/Mac usa `export` en vez de `set`.

La app quedará disponible en `http://127.0.0.1:5000/` y mostrará el texto **"Hola, Flask!"** en la ruta raíz (`/`).


