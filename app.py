import os
from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

# PostgreSQL (compatible con Python 3.14)
try:
    import psycopg
    from psycopg.rows import dict_row

    USAR_DB = True
    print("PSYCOPG CARGADO CORRECTAMENTE")

except Exception as e:
    print("ERROR PSYCOPG:", e)
    USAR_DB = False

app = Flask(__name__)

# Variable de entorno de Render
DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)

def get_db():
    """Conectar a PostgreSQL"""

    if not USAR_DB or not DATABASE_URL:
        return None

    return psycopg.connect(DATABASE_URL)


def init_db():
    """Crear tabla si no existe"""

    conn = get_db()

    if conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS comentarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                campus VARCHAR(100),
                comentario TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        cur.close()
        conn.close()


def obtener_comentarios():
    """Leer comentarios"""

    conn = get_db()

    if not conn:
        return []

    cur = conn.cursor(row_factory=dict_row)

    cur.execute("""
        SELECT *
        FROM comentarios
        ORDER BY fecha DESC
        LIMIT 50
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def guardar_comentario(nombre, campus, comentario):
    """Guardar comentario"""

    conn = get_db()

    if not conn:
        return False

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO comentarios
        (nombre, campus, comentario)
        VALUES (%s,%s,%s)
        """,
        (nombre, campus, comentario)
    )

    conn.commit()

    cur.close()
    conn.close()

    return True


TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Practica 06</title>
</head>
<body>

<h1>Servicios en la Nube - PaaS</h1>

<p>
Base de datos:
{{ 'Conectada (PostgreSQL)' if db_ok else 'No disponible' }}
</p>

{% if db_ok %}

<form method="POST">

<input name="nombre" placeholder="Nombre" required>

<select name="campus">
<option>TecNM Tampico</option>
<option>TecNM Altamira</option>
<option>Otro</option>
</select>

<textarea name="comentario" required></textarea>

<button type="submit">
Publicar
</button>

</form>

<h3>Comentarios</h3>

{% for c in comentarios %}

<div>

<strong>{{ c['nombre'] }}</strong>
- {{ c['campus'] }}

<p>{{ c['comentario'] }}</p>

<small>
{{ c['fecha'].strftime('%d/%m/%Y %H:%M') if c['fecha'] else '' }}
</small>

</div>

<hr>

{% endfor %}

{% else %}

<p>
La base de datos no está conectada.
</p>

{% endif %}

</body>
</html>
"""


@app.route("/", methods=["GET","POST"])
def index():

    init_db()

    if request.method == "POST":

        nombre = request.form.get("nombre","")
        campus = request.form.get("campus","")
        comentario = request.form.get("comentario","")

        if nombre and comentario:
            guardar_comentario(nombre,campus,comentario)

        return redirect(url_for("index"))

    comentarios = obtener_comentarios()

    db_ok = USAR_DB and bool(DATABASE_URL)

    return render_template_string(
        TEMPLATE,
        comentarios=comentarios,
        db_ok=db_ok
    )


@app.route("/api/status")
def status():

    return {
        "status":"ok",
        "plataforma":"Render.com",
        "modelo":"PaaS",

        "base_datos":
            "conectada"
            if (USAR_DB and DATABASE_URL)
            else "no configurada",

        "usar_db": USAR_DB,
        "database_url_existe": bool(DATABASE_URL),

        "framework":"Flask",
        "python":
            os.popen("python3 --version")
            .read()
            .strip()
    }


if __name__ == "__main__":

    port = int(os.getenv("PORT",5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
