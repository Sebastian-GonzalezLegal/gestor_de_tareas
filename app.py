from flask import Flask, request, redirect, url_for, render_template
import json
import os

# Lista global de tareas en memoria
tareas = []
ultimo_id = 0
RUTA_DATOS = "tareas.json"


def cargar_tareas() -> None:
    """Carga las tareas desde el archivo JSON, si existe."""
    global tareas, ultimo_id
    if not os.path.exists(RUTA_DATOS):
        tareas = []
        ultimo_id = 0
        return

    try:
        with open(RUTA_DATOS, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, OSError):
        tareas = []
        ultimo_id = 0
        return

    # Aseguramos estructura esperada
    tareas = [
        {
            "id": int(t.get("id", 0)),
            "texto": str(t.get("texto", "")),
            "completada": bool(t.get("completada", False)),
            "motivo": str(t.get("motivo", "")),
            "inhabilitada": bool(t.get("inhabilitada", False)),
            "lista": str(t.get("lista", "general")) or "general",
            "tema": str(t.get("tema", "")),
        }
        for t in datos
    ]
    ultimo_id = max((t["id"] for t in tareas), default=0)


def guardar_tareas() -> None:
    """Guarda las tareas actuales en el archivo JSON."""
    try:
        with open(RUTA_DATOS, "w", encoding="utf-8") as f:
            json.dump(tareas, f, ensure_ascii=False, indent=2)
    except OSError:
        # Para este ejemplo simple, sólo ignoramos errores de escritura.
        pass


def obtener_listas() -> list[str]:
    """Devuelve la lista de nombres de listas distintas."""
    nombres = {t.get("lista", "general") or "general" for t in tareas}
    if not nombres:
        return ["general"]
    # Nos aseguramos de que siempre exista al menos 'general'
    nombres.add("general")
    return sorted(nombres)


def construir_resumen_listas() -> list[dict]:
    """Construye un resumen con estadísticas de cada lista."""
    resumen = []
    for nombre in obtener_listas():
        tareas_de_lista = [t for t in tareas if (t.get("lista", "general") or "general") == nombre]
        total = len(tareas_de_lista)
        activas = len([t for t in tareas_de_lista if not t.get("inhabilitada")])
        completadas = len([t for t in tareas_de_lista if t.get("completada")])
        # Tema: usamos el primer tema no vacío encontrado
        tema = next((t.get("tema", "") for t in tareas_de_lista if t.get("tema")), "")
        resumen.append(
            {
                "nombre": nombre,
                "total": total,
                "activas": activas,
                "completadas": completadas,
                "tema": tema,
            }
        )
    return resumen


def obtener_tema_lista(nombre_lista: str) -> str:
    """Devuelve el tema de una lista (primer tema no vacío)."""
    tareas_de_lista = [
        t for t in tareas if (t.get("lista", "general") or "general") == nombre_lista
    ]
    return next((t.get("tema", "") for t in tareas_de_lista if t.get("tema")), "")


def agregar_tarea(texto: str, lista: str = "general") -> dict:
    """
    Agrega una tarea a la lista global.

    :param texto: Descripción de la tarea.
    :return: La tarea creada con su id incremental.
    """
    global ultimo_id
    ultimo_id += 1
    lista_normalizada = lista or "general"
    tarea = {
        "id": ultimo_id,
        "texto": texto,
        "completada": False,
        "motivo": "",
        "inhabilitada": False,
        "lista": lista_normalizada,
        "tema": "",
    }
    tareas.append(tarea)
    guardar_tareas()
    return tarea


def completar_tarea(tarea_id: int) -> bool:
    """
    Marca como completada la tarea con el id dado.

    :param tarea_id: Id numérico de la tarea.
    :return: True si se encontró y completó, False en caso contrario.
    """
    for tarea in tareas:
        if tarea["id"] == tarea_id:
            if tarea.get("inhabilitada"):
                return False
            tarea["completada"] = True
            tarea["motivo"] = ""
            guardar_tareas()
            return True
    return False


def marcar_incompleta(tarea_id: int, motivo: str = "") -> bool:
    """
    Marca como incompleta la tarea y opcionalmente guarda un motivo.
    """
    for tarea in tareas:
        if tarea["id"] == tarea_id:
            if tarea.get("inhabilitada"):
                return False
            tarea["completada"] = False
            tarea["motivo"] = motivo
            guardar_tareas()
            return True
    return False


def borrar_tarea(tarea_id: int) -> bool:
    """
    Marca una tarea como inhabilitada (borrado lógico) por su id.
    """
    for tarea in tareas:
        if tarea["id"] == tarea_id:
            tarea["inhabilitada"] = True
            guardar_tareas()
            return True
    return False


def create_app():
    """Aplicación Flask básica."""
    app = Flask(__name__)

    # Cargar las tareas desde disco al iniciar la aplicación
    cargar_tareas()

    @app.route("/")
    def index():
        """Página principal: listado de listas con estadísticas (ABM)."""
        listas = construir_resumen_listas()
        return render_template("listas.html", listas=listas)

    @app.route("/listas")
    def vista_listas():
        """Alias de la vista principal de listas."""
        listas = construir_resumen_listas()
        return render_template("listas.html", listas=listas)

    @app.route("/tareas")
    def vista_tareas():
        """Vista de tareas para una lista concreta."""
        # Determina la lista actual a mostrar
        lista_actual = request.args.get("lista", "general")
        # Filtra tareas por lista
        tareas_filtradas = [
            t for t in tareas if (t.get("lista", "general") or "general") == lista_actual
        ]
        listas = obtener_listas()
        tema_lista = obtener_tema_lista(lista_actual)
        # Renderiza la plantilla HTML pasando la lista de tareas y listas disponibles
        return render_template(
            "index.html",
            tareas=tareas_filtradas,
            lista_actual=lista_actual,
            listas=listas,
            tema_lista=tema_lista,
        )

    @app.route("/agregar", methods=["POST"])
    def ruta_agregar_tarea():
        """Ruta para agregar una nueva tarea usando el formulario."""
        texto = request.form.get("texto", "").strip()
        lista = request.args.get("lista", "general")
        if texto:
            agregar_tarea(texto, lista)
        return redirect(url_for("vista_tareas", lista=lista))

    @app.route("/completar/<int:tarea_id>", methods=["POST"])
    def ruta_completar_tarea(tarea_id: int):
        """Ruta para marcar una tarea como completada."""
        lista = request.args.get("lista", "general")
        completar_tarea(tarea_id)
        return redirect(url_for("vista_tareas", lista=lista))

    @app.route("/incompleta/<int:tarea_id>", methods=["POST"])
    def ruta_marcar_incompleta(tarea_id: int):
        """Ruta para marcar una tarea como incompleta y guardar motivo opcional."""
        lista = request.args.get("lista", "general")
        motivo = request.form.get("motivo", "").strip()
        marcar_incompleta(tarea_id, motivo)
        return redirect(url_for("vista_tareas", lista=lista))

    @app.route("/borrar/<int:tarea_id>", methods=["POST"])
    def ruta_borrar_tarea(tarea_id: int):
        """Ruta para eliminar una tarea."""
        lista = request.args.get("lista", "general")
        borrar_tarea(tarea_id)
        return redirect(url_for("vista_tareas", lista=lista))

    @app.route("/listas/crear", methods=["POST"])
    def crear_lista():
        """Crea (o navega a) una nueva lista por nombre."""
        nombre = request.form.get("nombre", "").strip() or "general"
        return redirect(url_for("vista_tareas", lista=nombre))

    @app.route("/listas/renombrar/<lista_nombre>", methods=["POST"])
    def renombrar_lista(lista_nombre: str):
        """Renombra una lista cambiando el campo 'lista' de las tareas."""
        nuevo_nombre = request.form.get("nuevo_nombre", "").strip()
        if not nuevo_nombre or nuevo_nombre == lista_nombre:
            return redirect(url_for("vista_listas"))
        for tarea in tareas:
            if (tarea.get("lista", "general") or "general") == lista_nombre:
                tarea["lista"] = nuevo_nombre
        guardar_tareas()
        return redirect(url_for("vista_listas"))

    @app.route("/listas/eliminar/<lista_nombre>", methods=["POST"])
    def eliminar_lista(lista_nombre: str):
        """
        Elimina una lista borrando definitivamente sus tareas.
        No permite eliminar la lista 'general'.
        """
        if lista_nombre == "general":
            return redirect(url_for("vista_listas"))

        global tareas
        tareas = [
            t
            for t in tareas
            if (t.get("lista", "general") or "general") != lista_nombre
        ]
        guardar_tareas()
        return redirect(url_for("vista_listas"))

    @app.route("/listas/tema/<lista_nombre>", methods=["POST"])
    def actualizar_tema_lista(lista_nombre: str):
        """Actualiza el tema de una lista (se guarda en cada tarea de esa lista)."""
        nuevo_tema = request.form.get("tema", "").strip()
        for tarea in tareas:
            if (tarea.get("lista", "general") or "general") == lista_nombre:
                tarea["tema"] = nuevo_tema
        guardar_tareas()
        return redirect(url_for("vista_listas"))

    return app


if __name__ == "__main__":
    # Ejecutar con: python app.py
    app = create_app()
    app.run(debug=True)

