from database.db import get_connection

def obtener_noticias():
    conn = get_connection()
    noticias = conn.execute("SELECT * FROM noticias ORDER BY fecha DESC").fetchall()
    conn.close()
    return noticias

def agregar_noticia(titulo, contenido, enlace):
    conn = get_connection()
    conn.execute(
        "INSERT INTO noticias (titulo, contenido, enlace) VALUES (?, ?, ?)",
        (titulo, contenido, enlace)
    )
    conn.commit()
    conn.close()