from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import hashlib
import re

app = Flask(__name__)
app.secret_key = 'sucesos_y_mas_2024_secreto_universitario'

LIMITE_CANTIDAD = 10

# Catálogo de servicios
CATALOGO = [
    {
        'id': 1, 'nombre': 'Auditoría de Ciberseguridad',
        'slug': 'auditoria-ciberseguridad', 'categoria': 'Seguridad',
        'icono': 'fas fa-shield-virus',
        'descripcion': 'Evaluación exhaustiva de vulnerabilidades, análisis de riesgos y recomendaciones para proteger tu infraestructura contra amenazas actuales.',
        'precio': 1500.00, 'unidad': 'por proyecto', 'duracion': '5–7 días hábiles', 'popular': True,
        'incluye': [
            'Escaneo de vulnerabilidades (OWASP Top 10)',
            'Prueba de penetración (Pentesting ético)',
            'Informe ejecutivo + informe técnico',
            'Reunión de presentación de resultados',
            '30 días de seguimiento post-auditoría',
        ],
    },
    {
        'id': 2, 'nombre': 'Desarrollo Web Corporativo',
        'slug': 'desarrollo-web', 'categoria': 'Desarrollo',
        'icono': 'fas fa-code',
        'descripcion': 'Sitio web o aplicación corporativa con diseño moderno, optimizado para SEO y con panel de administración incluido.',
        'precio': 2200.00, 'unidad': 'por sitio', 'duracion': '15–25 días hábiles', 'popular': True,
        'incluye': [
            'Diseño UI/UX personalizado',
            'Hasta 8 páginas o secciones',
            'Panel de administración de contenido',
            'Integración con Google Analytics',
            'SSL, hosting guiado y mantenimiento 30 días',
        ],
    },
    {
        'id': 3, 'nombre': 'Infraestructura Docker',
        'slug': 'infraestructura-docker', 'categoria': 'Infraestructura',
        'icono': 'fab fa-docker',
        'descripcion': 'Diseño e implementación de arquitectura en contenedores con Docker y Docker Compose para máxima escalabilidad y portabilidad.',
        'precio': 950.00, 'unidad': 'por servidor', 'duracion': '3–5 días hábiles', 'popular': False,
        'incluye': [
            'Dockerización de hasta 5 servicios',
            'Configuración de Docker Compose',
            'Variables de entorno y secretos seguros',
            'Pipeline CI/CD básico (GitHub Actions)',
            'Documentación técnica del entorno',
        ],
    },
    {
        'id': 4, 'nombre': 'Soporte Técnico Mensual',
        'slug': 'soporte-mensual', 'categoria': 'Soporte',
        'icono': 'fas fa-headset',
        'descripcion': 'Plan de mantenimiento preventivo mensual para servidores Linux, aplicaciones web y equipos de red corporativos.',
        'precio': 350.00, 'unidad': 'por mes', 'duracion': 'Contrato mensual', 'popular': False,
        'incluye': [
            'Monitoreo 24/7 de servicios críticos',
            'Actualizaciones de seguridad del SO',
            'Backup automático verificado',
            'Hasta 8 horas de atención remota',
            'Reporte mensual de estado del sistema',
        ],
    },
    {
        'id': 5, 'nombre': 'Consultoría IT (por hora)',
        'slug': 'consultoria-it', 'categoria': 'Consultoría',
        'icono': 'fas fa-user-tie',
        'descripcion': 'Sesiones con especialistas certificados en ciberseguridad, infraestructura y transformación digital para tu empresa.',
        'precio': 150.00, 'unidad': 'por hora', 'duracion': 'Agendable en 24h', 'popular': False,
        'incluye': [
            'Consultor senior certificado',
            'Grabación de sesión (opcional)',
            'Resumen escrito de recomendaciones',
            'Disponibilidad Lun–Sab 8AM–8PM',
            'Primera hora con 20% de descuento',
        ],
    },
    {
        'id': 6, 'nombre': 'Análisis Forense Digital',
        'slug': 'forense-digital', 'categoria': 'Seguridad',
        'icono': 'fas fa-search',
        'descripcion': 'Investigación de incidentes de seguridad, recuperación de evidencia digital e informes periciales para uso legal o interno.',
        'precio': 1200.00, 'unidad': 'por caso', 'duracion': '3–10 días hábiles', 'popular': False,
        'incluye': [
            'Adquisición forense de imágenes de disco',
            'Análisis de logs y timeline de eventos',
            'Identificación del vector de ataque',
            'Informe pericial con validez legal',
            'Recomendaciones de remediación',
        ],
    },
    {
        'id': 7, 'nombre': 'VPN Empresarial',
        'slug': 'vpn-empresarial', 'categoria': 'Infraestructura',
        'icono': 'fas fa-network-wired',
        'descripcion': 'Implementación de VPN corporativa con autenticación de dos factores para trabajo remoto y conexión entre sucursales.',
        'precio': 600.00, 'unidad': 'por implementación', 'duracion': '2–3 días hábiles', 'popular': False,
        'incluye': [
            'Servidor WireGuard o OpenVPN',
            'Autenticación 2FA integrada',
            'Hasta 25 usuarios incluidos',
            'Guía de configuración para empleados',
            'Soporte técnico 15 días post-instalación',
        ],
    },
    {
        'id': 8, 'nombre': 'Migración a la Nube (Cloud)',
        'slug': 'migracion-cloud', 'categoria': 'Cloud',
        'icono': 'fas fa-cloud-upload-alt',
        'descripcion': 'Migración completa de servidores locales a AWS, GCP o Azure con mínimo tiempo de inactividad y plan de contingencia.',
        'precio': 3500.00, 'unidad': 'por migración', 'duracion': '10–20 días hábiles', 'popular': True,
        'incluye': [
            'Evaluación de arquitectura actual',
            'Plan de migración sin riesgo de datos',
            'Configuración de balanceador de carga',
            'Auto-scaling y alta disponibilidad',
            'Capacitación al equipo técnico (4h)',
        ],
    },
]

CATEGORIAS = sorted(set(s['categoria'] for s in CATALOGO))

ESTADOS_COTIZACION = ['pendiente', 'en_proceso', 'pagado', 'finalizado', 'cancelado']


# Carrito disponible en todos los templates
@app.context_processor
def contexto_global():
    carrito = session.get('carrito', [])
    total_items = sum(i.get('cantidad', 1) for i in carrito)
    subtotal_carrito = sum(i['precio'] * i.get('cantidad', 1) for i in carrito)
    return {
        'carrito': carrito,
        'total_items_carrito': total_items,
        'subtotal_carrito': subtotal_carrito,
    }


# Base de datos
def obtener_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    conn = obtener_db()
    c = conn.cursor()

    # Noticias
    c.execute('''CREATE TABLE IF NOT EXISTS noticias (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo    TEXT NOT NULL,
        contenido TEXT NOT NULL,
        imagen    TEXT DEFAULT 'noticia-default.png',
        categoria TEXT DEFAULT 'General',
        fuente    TEXT DEFAULT '',
        fecha     TEXT NOT NULL
    )''')

    # Clientes
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre      TEXT NOT NULL,
        logo        TEXT DEFAULT 'cliente-default.png',
        descripcion TEXT DEFAULT '',
        sector      TEXT DEFAULT 'Tecnología'
    )''')

    # Cotizaciones
    c.execute('''CREATE TABLE IF NOT EXISTS cotizaciones (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia     TEXT NOT NULL,
        fecha          TEXT NOT NULL,
        subtotal       REAL NOT NULL,
        itbms          REAL NOT NULL,
        total          REAL NOT NULL,
        estado         TEXT DEFAULT 'pendiente',
        metodo_pago    TEXT DEFAULT '',
        cliente_nombre TEXT DEFAULT '',
        cliente_correo TEXT DEFAULT ''
    )''')

    # Detalle de cada cotización
    c.execute('''CREATE TABLE IF NOT EXISTS detalle_cotizacion (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cotizacion_id   INTEGER NOT NULL,
        servicio        TEXT NOT NULL,
        cantidad        INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        subtotal_linea  REAL NOT NULL,
        FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
    )''')

    # Transacciones de pago
    c.execute('''CREATE TABLE IF NOT EXISTS transacciones (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        cotizacion_id    INTEGER NOT NULL,
        referencia_pago  TEXT NOT NULL,
        metodo_pago      TEXT NOT NULL,
        monto            REAL NOT NULL,
        fecha            TEXT NOT NULL,
        estado           TEXT DEFAULT 'aprobado',
        FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
    )''')

    # Columnas de compatibilidad (bases existentes)
    for alter in [
        'ALTER TABLE noticias ADD COLUMN fuente TEXT DEFAULT ""',
        'ALTER TABLE cotizaciones ADD COLUMN metodo_pago TEXT DEFAULT ""',
        'ALTER TABLE cotizaciones ADD COLUMN cliente_nombre TEXT DEFAULT ""',
        'ALTER TABLE cotizaciones ADD COLUMN cliente_correo TEXT DEFAULT ""',
    ]:
        try:
            c.execute(alter)
        except sqlite3.OperationalError:
            pass

    # Datos de ejemplo
    if not c.execute('SELECT 1 FROM noticias').fetchone():
        c.executemany(
            'INSERT INTO noticias (titulo,contenido,imagen,categoria,fuente,fecha) VALUES (?,?,?,?,?,?)',
            [
                ('Nueva amenaza: ransomware dirigido a PYMEs panameñas',
                 'Se detectaron campañas activas de ransomware apuntando a pequeñas y medianas empresas en Panamá. SUCESOS y MÁS recomienda revisar políticas de acceso y realizar copias de seguridad inmediatas.',
                 'noticia1.png', 'Ciberseguridad', 'https://www.eset.com/latam/', '2024-11-20'),
                ('Docker 26 trae mejoras de seguridad significativas',
                 'La versión 26 de Docker introduce aislamiento mejorado de red, escaneo automático de imágenes con CVE integrado y soporte para rootless containers en producción.',
                 'noticia2.png', 'Infraestructura', 'https://docs.docker.com', '2024-11-12'),
                ('SUCESOS y MÁS certifica a 4 ingenieros en AWS Security',
                 'El equipo amplía capacidades con la certificación AWS Certified Security Specialty, reforzando la oferta de migración y seguridad en la nube para clientes corporativos.',
                 'noticia3.png', 'Empresa', '', '2024-11-05'),
            ]
        )

    if not c.execute('SELECT 1 FROM clientes').fetchone():
        c.executemany(
            'INSERT INTO clientes (nombre,logo,descripcion,sector) VALUES (?,?,?,?)',
            [
                ('TechCorp Panamá',   'cliente1.png', 'Consultoría tecnológica empresarial', 'Consultoría'),
                ('Banco Digital PA',  'cliente2.png', 'Servicios financieros y fintech',     'Finanzas'),
                ('LogisPanamá',       'cliente3.png', 'Logística y cadena de suministro',    'Logística'),
                ('MedTech Solutions', 'cliente4.png', 'Dispositivos y software médico',      'Salud'),
                ('GovSec Panama',     'cliente5.png', 'Seguridad digital gubernamental',     'Gobierno'),
                ('StartHub PTY',      'cliente6.png', 'Ecosistema de startups',              'Startups'),
            ]
        )

    conn.commit()
    conn.close()


# Rutas principales
@app.route('/')
def index():
    conn = obtener_db()
    noticias = conn.execute('SELECT * FROM noticias ORDER BY fecha DESC LIMIT 3').fetchall()
    clientes = conn.execute('SELECT * FROM clientes LIMIT 6').fetchall()
    conn.close()
    servicios_destacados = [s for s in CATALOGO if s['popular']]
    return render_template('index.html', noticias=noticias, clientes=clientes,
                           servicios_destacados=servicios_destacados)


@app.route('/clientes')
def clientes():
    conn = obtener_db()
    todos = conn.execute('SELECT * FROM clientes ORDER BY nombre').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=todos)


@app.route('/servicios')
def servicios():
    cat = request.args.get('categoria', 'Todos')
    lista = [s for s in CATALOGO if s['categoria'] == cat] if cat != 'Todos' else CATALOGO
    return render_template('servicios.html', servicios=lista,
                           categorias=CATEGORIAS, categoria_activa=cat)


@app.route('/servicios/<slug>')
def detalle_servicio(slug):
    servicio = next((s for s in CATALOGO if s['slug'] == slug), None)
    if not servicio:
        flash('No encontramos ese servicio.', 'error')
        return redirect(url_for('servicios'))
    return render_template('detalle_servicio.html', servicio=servicio)


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        correo   = request.form.get('correo', '').strip()
        mensaje  = request.form.get('mensaje', '').strip()
        terminos = request.form.get('terminos')

        errores = []
        if len(nombre) < 3:
            errores.append('El nombre debe tener al menos 3 caracteres.')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', correo):
            errores.append('El correo no parece válido.')
        if len(mensaje) < 20:
            errores.append('El mensaje debe tener al menos 20 caracteres.')
        if not terminos:
            errores.append('Debes aceptar la política de privacidad para continuar.')

        if errores:
            for e in errores:
                flash(e, 'error')
            return redirect(url_for('contacto'))

        flash(f'Gracias, {nombre.split()[0]}. Tu mensaje fue recibido y te contactaremos pronto.', 'exito')
        return redirect(url_for('contacto'))

    return render_template('contacto.html')


@app.route('/ubicacion')
def ubicacion():
    return render_template('ubicacion.html')


# Carrito
@app.route('/cotizacion/agregar/<int:sid>', methods=['POST'])
def agregar_cotizacion(sid):
    srv = next((s for s in CATALOGO if s['id'] == sid), None)
    if not srv:
        flash('Ese servicio no existe.', 'error')
        return redirect(url_for('servicios'))

    carrito = session.get('carrito', [])
    for item in carrito:
        if item['id'] == sid:
            nueva_cant = item['cantidad'] + 1
            if nueva_cant > LIMITE_CANTIDAD:
                flash(f'Para cantidades mayores a {LIMITE_CANTIDAD} unidades, comunícate con nuestro equipo directamente.', 'limite')
                return redirect(url_for('contacto'))
            item['cantidad'] = nueva_cant
            session['carrito'] = carrito
            session.modified = True
            flash(f'Cantidad de "{srv["nombre"]}" actualizada a {nueva_cant}.', 'info')
            return redirect(request.referrer or url_for('servicios'))

    carrito.append({
        'id': srv['id'], 'nombre': srv['nombre'],
        'precio': srv['precio'], 'unidad': srv['unidad'], 'cantidad': 1,
    })
    session['carrito'] = carrito
    session.modified = True
    flash(f'"{srv["nombre"]}" fue agregado a tu cotización.', 'exito')
    return redirect(request.referrer or url_for('servicios'))


@app.route('/cotizacion/quitar/<int:sid>', methods=['POST'])
def quitar_cotizacion(sid):
    session['carrito'] = [i for i in session.get('carrito', []) if i['id'] != sid]
    session.modified = True
    flash('El servicio fue quitado de la cotización.', 'info')
    return redirect(url_for('cotizacion'))


@app.route('/cotizacion/actualizar/<int:sid>', methods=['POST'])
def actualizar_cantidad(sid):
    try:
        cantidad = int(request.form.get('cantidad', 1))
    except ValueError:
        flash('La cantidad ingresada no es válida.', 'error')
        return redirect(url_for('cotizacion'))

    if cantidad > LIMITE_CANTIDAD:
        flash(f'Para cantidades mayores a {LIMITE_CANTIDAD} unidades, comunícate con nuestro equipo.', 'limite')
        return redirect(url_for('contacto'))

    cantidad = max(1, cantidad)
    carrito = session.get('carrito', [])
    for item in carrito:
        if item['id'] == sid:
            item['cantidad'] = cantidad
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('cotizacion'))


@app.route('/cotizacion/limpiar')
def limpiar_cotizacion():
    session.pop('carrito', None)
    flash('La cotización fue vaciada.', 'info')
    return redirect(url_for('servicios'))


@app.route('/cotizacion')
def cotizacion():
    items    = session.get('carrito', [])
    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    itbms    = round(subtotal * 0.07, 2)
    total    = subtotal + itbms
    return render_template('cotizacion.html', items=items,
                           subtotal=subtotal, itbms=itbms, total=total,
                           limite=LIMITE_CANTIDAD)


# Confirmar cotización → guarda en DB con estado 'pendiente' → redirige a pago
@app.route('/cotizacion/confirmar', methods=['POST'])
def confirmar_cotizacion():
    items = session.get('carrito', [])

    if not items:
        flash('No hay servicios en la cotización. Agrega al menos uno antes de continuar.', 'error')
        return redirect(url_for('servicios'))

    for item in items:
        if item.get('cantidad', 1) > LIMITE_CANTIDAD:
            flash(f'El servicio "{item["nombre"]}" supera el límite de {LIMITE_CANTIDAD} unidades. Para pedidos grandes, contáctanos.', 'limite')
            return redirect(url_for('contacto'))

    cliente_nombre = request.form.get('cliente_nombre', '').strip()
    cliente_correo = request.form.get('cliente_correo', '').strip()

    if len(cliente_nombre) < 2:
        flash('Ingresa tu nombre para continuar.', 'error')
        return redirect(url_for('cotizacion'))
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', cliente_correo):
        flash('Ingresa un correo electrónico válido.', 'error')
        return redirect(url_for('cotizacion'))

    subtotal = sum(i['precio'] * i['cantidad'] for i in items)
    itbms    = round(subtotal * 0.07, 2)
    total    = round(subtotal + itbms, 2)

    hoy = datetime.now()
    hash_c    = hashlib.md5(f"{hoy}{total}{len(items)}".encode()).hexdigest()[:5].upper()
    referencia = f"COT-{hoy.strftime('%Y%m%d')}-{hash_c}"

    conn = obtener_db()
    try:
        cur = conn.execute(
            '''INSERT INTO cotizaciones
               (referencia, fecha, subtotal, itbms, total, estado, cliente_nombre, cliente_correo)
               VALUES (?,?,?,?,?,?,?,?)''',
            (referencia, hoy.strftime('%Y-%m-%d %H:%M'), subtotal, itbms, total,
             'pendiente', cliente_nombre, cliente_correo)
        )
        cotizacion_id = cur.lastrowid

        for item in items:
            conn.execute(
                '''INSERT INTO detalle_cotizacion
                   (cotizacion_id, servicio, cantidad, precio_unitario, subtotal_linea)
                   VALUES (?,?,?,?,?)''',
                (cotizacion_id, item['nombre'], item['cantidad'],
                 item['precio'], round(item['precio'] * item['cantidad'], 2))
            )

        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        flash('No se pudo registrar la solicitud. Inténtalo de nuevo.', 'error')
        return redirect(url_for('cotizacion'))

    # Mantener carrito en sesión hasta que se complete el pago
    session['cotizacion_pendiente_id'] = cotizacion_id
    return redirect(url_for('pago', cot_id=cotizacion_id))


# Pantalla de pago simulado
@app.route('/pago/<int:cot_id>', methods=['GET', 'POST'])
def pago(cot_id):
    conn = obtener_db()
    cot = conn.execute('SELECT * FROM cotizaciones WHERE id=?', (cot_id,)).fetchone()

    if not cot:
        conn.close()
        flash('No se encontró esa cotización.', 'error')
        return redirect(url_for('index'))

    if cot['estado'] not in ('pendiente',):
        # Ya fue procesada, ir directo a factura
        conn.close()
        return redirect(url_for('ver_factura', cot_id=cot_id))

    if request.method == 'POST':
        metodo = request.form.get('metodo_pago', '').strip()
        if metodo not in ('tarjeta', 'transferencia', 'yappy'):
            conn.close()
            flash('Selecciona un método de pago válido.', 'error')
            return redirect(url_for('pago', cot_id=cot_id))

        # Generar referencia de transacción
        ref_pago = f"PAG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{cot_id}"

        # Guardar transacción
        conn.execute(
            '''INSERT INTO transacciones
               (cotizacion_id, referencia_pago, metodo_pago, monto, fecha, estado)
               VALUES (?,?,?,?,?,?)''',
            (cot_id, ref_pago, metodo, cot['total'],
             datetime.now().strftime('%Y-%m-%d %H:%M'), 'aprobado')
        )

        # Actualizar estado y método de pago en la cotización
        metodo_legible = {'tarjeta': 'Tarjeta de crédito/débito',
                          'transferencia': 'Transferencia bancaria',
                          'yappy': 'Yappy'}.get(metodo, metodo)
        conn.execute(
            'UPDATE cotizaciones SET estado=?, metodo_pago=? WHERE id=?',
            ('pagado', metodo_legible, cot_id)
        )
        conn.commit()
        conn.close()

        # Limpiar carrito
        session.pop('carrito', None)
        session.pop('cotizacion_pendiente_id', None)

        flash('La compra de prueba fue registrada correctamente.', 'exito')
        return redirect(url_for('ver_factura', cot_id=cot_id))

    detalles = conn.execute(
        'SELECT * FROM detalle_cotizacion WHERE cotizacion_id=?', (cot_id,)
    ).fetchall()
    conn.close()

    return render_template('pago.html', cotizacion=cot, detalles=detalles)


# Factura desde base de datos
@app.route('/factura/<int:cot_id>')
def ver_factura(cot_id):
    conn = obtener_db()
    cot = conn.execute('SELECT * FROM cotizaciones WHERE id=?', (cot_id,)).fetchone()
    if not cot:
        conn.close()
        flash('No se encontró esa factura.', 'error')
        return redirect(url_for('index'))

    detalles = conn.execute(
        'SELECT * FROM detalle_cotizacion WHERE cotizacion_id=?', (cot_id,)
    ).fetchall()

    transaccion = conn.execute(
        'SELECT * FROM transacciones WHERE cotizacion_id=? ORDER BY id DESC LIMIT 1', (cot_id,)
    ).fetchone()
    conn.close()

    qr_data = f"https://sucesosymas.com/verificar/{cot['referencia']}"
    qr_url  = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={qr_data}&bgcolor=ffffff&color=1e40af&qzone=1"

    try:
        fecha_obj = datetime.strptime(cot['fecha'], '%Y-%m-%d %H:%M')
    except ValueError:
        fecha_obj = datetime.now()

    return render_template('factura.html',
        cotizacion=cot,
        detalles=detalles,
        transaccion=transaccion,
        qr_url=qr_url,
        numero_factura=cot['referencia'],
        fecha_emision=fecha_obj.strftime('%d/%m/%Y'),
        fecha_vencimiento=(fecha_obj + timedelta(days=30)).strftime('%d/%m/%Y'),
        desde_db=True
    )


# Factura demo (sin cotización activa)
@app.route('/factura')
def factura():
    if session.get('carrito'):
        return redirect(url_for('cotizacion'))

    servicios_f = [
        {'servicio': 'Auditoría de Ciberseguridad',          'cantidad': 1, 'precio_unitario': 1500.00, 'subtotal_linea': 1500.00},
        {'servicio': 'Infraestructura Docker (2 servidores)', 'cantidad': 2, 'precio_unitario': 950.00,  'subtotal_linea': 1900.00},
        {'servicio': 'Desarrollo Web Corporativo',            'cantidad': 1, 'precio_unitario': 2200.00, 'subtotal_linea': 2200.00},
        {'servicio': 'Soporte Técnico Mensual (3 meses)',     'cantidad': 3, 'precio_unitario': 350.00,  'subtotal_linea': 1050.00},
    ]
    subtotal = sum(s['subtotal_linea'] for s in servicios_f)
    itbms    = round(subtotal * 0.07, 2)
    total    = round(subtotal + itbms, 2)
    hoy      = datetime.now()
    ref      = f"DEMO-{hoy.strftime('%Y%m')}-XXXX"
    qr_url   = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=DEMO&bgcolor=ffffff&color=1e40af&qzone=1"
    cot_demo = {'referencia': ref, 'subtotal': subtotal, 'itbms': itbms, 'total': total,
                'estado': 'demo', 'metodo_pago': '—', 'cliente_nombre': 'Cliente Ejemplo',
                'cliente_correo': 'ejemplo@email.com'}

    return render_template('factura.html',
        cotizacion=cot_demo, detalles=servicios_f, transaccion=None,
        qr_url=qr_url, numero_factura=ref,
        fecha_emision=hoy.strftime('%d/%m/%Y'),
        fecha_vencimiento=(hoy + timedelta(days=30)).strftime('%d/%m/%Y'),
        desde_db=False
    )


# Admin — CRUD noticias, clientes, gestión de cotizaciones
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = obtener_db()

    if request.method == 'POST':
        accion = request.form.get('accion', '')

        # Noticias
        if accion == 'agregar_noticia':
            titulo    = request.form.get('titulo', '').strip()
            contenido = request.form.get('contenido', '').strip()
            imagen    = request.form.get('imagen', 'noticia-default.png').strip() or 'noticia-default.png'
            categoria = request.form.get('categoria', 'General').strip()
            fuente    = request.form.get('fuente', '').strip()
            errores = []
            if len(titulo) < 10:   errores.append('El título debe tener al menos 10 caracteres.')
            if len(titulo) > 120:  errores.append('El título no puede superar 120 caracteres.')
            if len(contenido) < 30: errores.append('El contenido debe tener al menos 30 caracteres.')
            if len(contenido) > 2000: errores.append('El contenido no puede superar 2000 caracteres.')
            if errores:
                for e in errores: flash(e, 'error')
            else:
                conn.execute(
                    'INSERT INTO noticias (titulo,contenido,imagen,categoria,fuente,fecha) VALUES (?,?,?,?,?,?)',
                    (titulo, contenido, imagen, categoria, fuente, datetime.now().strftime('%Y-%m-%d'))
                )
                conn.commit()
                flash('La noticia se guardó correctamente.', 'exito')

        elif accion == 'editar_noticia':
            nid       = request.form.get('noticia_id', '').strip()
            titulo    = request.form.get('titulo', '').strip()
            contenido = request.form.get('contenido', '').strip()
            categoria = request.form.get('categoria', 'General').strip()
            fuente    = request.form.get('fuente', '').strip()
            errores = []
            if not nid: errores.append('No se identificó la noticia.')
            if len(titulo) < 10:   errores.append('El título debe tener al menos 10 caracteres.')
            if len(titulo) > 120:  errores.append('El título no puede superar 120 caracteres.')
            if len(contenido) < 30: errores.append('El contenido debe tener al menos 30 caracteres.')
            if len(contenido) > 2000: errores.append('El contenido no puede superar 2000 caracteres.')
            if errores:
                for e in errores: flash(e, 'error')
            else:
                conn.execute(
                    'UPDATE noticias SET titulo=?,contenido=?,categoria=?,fuente=? WHERE id=?',
                    (titulo, contenido, categoria, fuente, nid)
                )
                conn.commit()
                flash('La noticia se actualizó correctamente.', 'exito')

        elif accion == 'eliminar_noticia':
            nid = request.form.get('noticia_id', '').strip()
            if nid:
                conn.execute('DELETE FROM noticias WHERE id=?', (nid,))
                conn.commit()
                flash('La noticia fue eliminada.', 'info')

        # Clientes
        elif accion == 'agregar_cliente':
            nombre      = request.form.get('cli_nombre', '').strip()
            logo        = request.form.get('cli_logo', 'cliente-default.png').strip() or 'cliente-default.png'
            descripcion = request.form.get('cli_descripcion', '').strip()
            sector      = request.form.get('cli_sector', 'Tecnología').strip()
            if len(nombre) < 2:
                flash('El nombre del cliente debe tener al menos 2 caracteres.', 'error')
            else:
                conn.execute(
                    'INSERT INTO clientes (nombre,logo,descripcion,sector) VALUES (?,?,?,?)',
                    (nombre, logo, descripcion, sector)
                )
                conn.commit()
                flash(f'El cliente "{nombre}" fue agregado.', 'exito')

        elif accion == 'editar_cliente':
            cid         = request.form.get('cliente_id', '').strip()
            nombre      = request.form.get('cli_nombre', '').strip()
            logo        = request.form.get('cli_logo', 'cliente-default.png').strip() or 'cliente-default.png'
            descripcion = request.form.get('cli_descripcion', '').strip()
            sector      = request.form.get('cli_sector', 'Tecnología').strip()
            if not cid or len(nombre) < 2:
                flash('No se pudo actualizar el cliente. Revisa los datos.', 'error')
            else:
                conn.execute(
                    'UPDATE clientes SET nombre=?,logo=?,descripcion=?,sector=? WHERE id=?',
                    (nombre, logo, descripcion, sector, cid)
                )
                conn.commit()
                flash(f'El cliente "{nombre}" fue actualizado.', 'exito')

        elif accion == 'eliminar_cliente':
            cid = request.form.get('cliente_id', '').strip()
            if cid:
                conn.execute('DELETE FROM clientes WHERE id=?', (cid,))
                conn.commit()
                flash('El cliente fue eliminado.', 'info')

        # Cambiar estado de cotización
        elif accion == 'actualizar_estado':
            cot_id = request.form.get('cot_id', '').strip()
            nuevo_estado = request.form.get('nuevo_estado', '').strip()
            if cot_id and nuevo_estado in ESTADOS_COTIZACION:
                conn.execute('UPDATE cotizaciones SET estado=? WHERE id=?', (nuevo_estado, cot_id))
                conn.commit()
                flash('El estado de la solicitud fue actualizado.', 'exito')
            else:
                flash('Estado no válido.', 'error')

        conn.close()
        return redirect(url_for('admin'))

    # GET
    noticias           = conn.execute('SELECT * FROM noticias ORDER BY fecha DESC').fetchall()
    todos_clientes     = conn.execute('SELECT * FROM clientes ORDER BY nombre').fetchall()
    cotizaciones       = conn.execute('SELECT * FROM cotizaciones ORDER BY id DESC LIMIT 20').fetchall()
    total_noticias     = conn.execute('SELECT COUNT(*) FROM noticias').fetchone()[0]
    total_clientes     = conn.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    total_cotizaciones = conn.execute('SELECT COUNT(*) FROM cotizaciones').fetchone()[0]
    conn.close()

    return render_template('admin.html',
                           noticias=noticias,
                           todos_clientes=todos_clientes,
                           cotizaciones=cotizaciones,
                           total_noticias=total_noticias,
                           total_clientes=total_clientes,
                           total_cotizaciones=total_cotizaciones,
                           total_servicios=len(CATALOGO),
                           estados=ESTADOS_COTIZACION)


if __name__ == '__main__':
    inicializar_db()
    app.run(debug=True, host='0.0.0.0')