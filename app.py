from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import json
import os
from datetime import datetime
import glob


app = Flask(__name__)

# Rutas de los archivos JSON
SOLICITUDES_FILE = 'solicitudes.json'
USUARIOS_FILE = 'usuarios_autorizados.json'
UPLOADS_FOLDER = 'uploads'

# Asegurar que la carpeta de uploads existe
os.makedirs(UPLOADS_FOLDER, exist_ok=True)

# Funciones de ayuda para leer y escribir archivos JSON
def leer_json(ruta_archivo):
    try:
        with open(ruta_archivo, 'r') as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return []

def escribir_json(ruta_archivo, datos):
    with open(ruta_archivo, 'w') as archivo:
        json.dump(datos, archivo, indent=4)

def crear_pdf_url(solicitud_id):
    pdf_url = None
    filename_prefix = f"{solicitud_id}_"
    pattern = os.path.join(UPLOADS_FOLDER, f"{filename_prefix}*.PDF")
    matching_files = glob.glob(pattern)

    if matching_files:
        pdf_filename = os.path.basename(matching_files[0])
        pdf_url = url_for('ver_pdf', filename=pdf_filename) # Usamos la nueva ruta 'ver_pdf'
    return pdf_url

# Nueva ruta para servir los archivos PDF desde la carpeta uploads
@app.route('/uploads/<filename>')
def ver_pdf(filename):
    return send_from_directory(UPLOADS_FOLDER, filename)

# Rutas de la aplicación
@app.route('/')
# def index():
#     solicitudes = leer_json(SOLICITUDES_FILE)
#     return render_template('index.html', solicitudes=solicitudes)
def index():
    solicitudes = leer_json(SOLICITUDES_FILE)

    # Obtener los parámetros de filtro de la URL
    filtro_numero_trabajo = request.args.get('numero_trabajo')
    filtro_solicitado_por = request.args.get('solicitado_por')
    filtro_fecha_desde_str = request.args.get('fecha_desde')
    filtro_fecha_hasta_str = request.args.get('fecha_hasta')

    # Aplicar los filtros
    solicitudes_filtradas = []
    for solicitud in solicitudes:
        cumple_filtro = True

        if filtro_numero_trabajo:
            if filtro_numero_trabajo.lower() not in solicitud['numero_trabajo'].lower():
                cumple_filtro = False

        if filtro_solicitado_por:
            if filtro_solicitado_por.lower() not in solicitud['solicitado_por'].lower():
                cumple_filtro = False

        if filtro_fecha_desde_str:
            try:
                filtro_fecha_desde = datetime.strptime(filtro_fecha_desde_str, '%Y-%m-%d').date()
                fecha_solicitud = datetime.fromisoformat(solicitud['fecha_solicitud']).date()
                if fecha_solicitud < filtro_fecha_desde:
                    cumple_filtro = False
            except ValueError:
                # Manejar el caso en que la fecha desde no sea válida
                pass

        if filtro_fecha_hasta_str:
            try:
                filtro_fecha_hasta = datetime.strptime(filtro_fecha_hasta_str, '%Y-%m-%d').date()
                fecha_solicitud = datetime.fromisoformat(solicitud['fecha_solicitud']).date()
                if fecha_solicitud > filtro_fecha_hasta:
                    cumple_filtro = False
            except ValueError:
                # Manejar el caso en que la fecha hasta no sea válida
                pass

        if cumple_filtro:
            solicitudes_filtradas.append(solicitud)

    return render_template('index.html', solicitudes=solicitudes_filtradas)


@app.route('/nueva_solicitud', methods=['GET', 'POST'])
def nueva_solicitud():
    if request.method == 'POST':
        solicitudes = leer_json(SOLICITUDES_FILE)
        nuevo_id = max((s['solicitud_id'] for s in solicitudes), default=0) + 1
        location = request.form.getlist('location')
        area = request.form['area']
        solicitado_por = request.form['solicitado_por']
        numero_trabajo = request.form['numero_trabajo']
        razon_reproceso = request.form.getlist('reason_rework')
        detalles_partes = []
        materiales = request.form.getlist('material')
        calibres = request.form.getlist('calibre')
        cantidades = request.form.getlist('cantidad')
        descripciones = request.form.getlist('descripcion')
        for material, calibre, cantidad, descripcion in zip(materiales, calibres, cantidades, descripciones):
            detalles_partes.append({'material': material, 'calibre': calibre, 'cantidad': int(cantidad), 'descripcion': descripcion})
        documentos = []
        if 'documentos' in request.files:
            files = request.files.getlist('documentos')
            for file in files:
                if file:
                    filename = f"{nuevo_id}_{file.filename}"
                    file.save(os.path.join(UPLOADS_FOLDER, filename))
                    documentos.append(filename)

        nueva_solicitud = {
            'solicitud_id': nuevo_id,
            'location': location,
            'area': area,
            'solicitado_por': solicitado_por,
            'fecha_solicitud': datetime.now().isoformat(),
            'numero_trabajo': numero_trabajo,
            'razon_reproceso': razon_reproceso,
            'detalles_partes': detalles_partes,
            'estatus_radicacion': 'In progress',
            'usuario_radicacion': request.form.get('usuario_radicacion'),
            'fecha_radicacion': datetime.now().isoformat(),
            'estatus_nest': None,
            'usuario_nest': None,
            'fecha_nest': None,
            'documentos_nest': documentos,
            'estatus_corte': None,
            'usuario_corte': None,
            'fecha_corte': None,
            'estatus_doblez': None,
            'usuario_doblez': None,
            'fecha_doblez': None,
            'estatus_finalizado': None,
            'usuario_finalizado': None,
            'fecha_finalizado': None,
        }
        solicitudes.append(nueva_solicitud)
        escribir_json(SOLICITUDES_FILE, solicitudes)
        return redirect(url_for('index'))
    return render_template('nueva_solicitud.html')

@app.route('/detalles_solicitud/<int:solicitud_id>', methods=['GET', 'POST'])
def detalles_solicitud(solicitud_id):
    solicitudes = leer_json(SOLICITUDES_FILE)
    solicitud = next((s for s in solicitudes if s['solicitud_id'] == solicitud_id), None)
    pdf_url = crear_pdf_url(solicitud_id)
    if not solicitud:
        return "Solicitud no encontrada", 404

    if request.method == 'POST':
        estatus_etapa = request.form['estatus_etapa']
        usuario_etapa = request.form['usuario_etapa']
        fecha_etapa = datetime.now().isoformat()
        if estatus_etapa == 'estatus_nest':
            solicitud['estatus_nest'] = request.form['estatus_nest_value']
            solicitud['usuario_nest'] = usuario_etapa
            solicitud['fecha_nest'] = fecha_etapa
        elif estatus_etapa == 'estatus_corte':
            solicitud['estatus_corte'] = request.form['estatus_corte_value']
            solicitud['usuario_corte'] = usuario_etapa
            solicitud['fecha_corte'] = fecha_etapa
        elif estatus_etapa == 'estatus_doblez':
            solicitud['estatus_doblez'] = request.form['estatus_doblez_value']
            solicitud['usuario_doblez'] = usuario_etapa
            solicitud['fecha_doblez'] = fecha_etapa
        elif estatus_etapa == 'estatus_finalizado':
            solicitud['estatus_finalizado'] = request.form['estatus_finalizado_value']
            solicitud['usuario_finalizado'] = usuario_etapa
            solicitud['fecha_finalizado'] = fecha_etapa

        if 'documentos_nest' in request.files:
            files = request.files.getlist('documentos_nest')
            for file in files:
                if file:
                    filename = f"{solicitud_id}_nest_{file.filename}"
                    file.save(os.path.join(UPLOADS_FOLDER, filename))
                    solicitud['documentos_nest'].append(filename)

        escribir_json(SOLICITUDES_FILE, solicitudes)
        return redirect(url_for('detalles_solicitud', solicitud_id=solicitud_id))

    return render_template('detalles_solicitud.html', solicitud=solicitud, pdf_url=pdf_url)

@app.route('/usuarios_autorizados', methods=['GET', 'POST'])
def usuarios_autorizados():
    usuarios = leer_json(USUARIOS_FILE)
    if request.method == 'POST':
        nuevo_usuario = request.form['nuevo_usuario']
        if nuevo_usuario not in usuarios:
            usuarios.append(nuevo_usuario)
            escribir_json(USUARIOS_FILE, usuarios)
        return redirect(url_for('usuarios_autorizados'))

    return render_template('usuarios_autorizados.html', usuarios=usuarios)

@app.route('/eliminar_usuario/<usuario>', methods=['POST'])
def eliminar_usuario(usuario):
    usuarios = leer_json(USUARIOS_FILE)
    if usuario in usuarios:
        usuarios.remove(usuario)
        escribir_json(USUARIOS_FILE, usuarios)
    return redirect(url_for('usuarios_autorizados'))


@app.route('/landing')
def landing():
    return render_template('landing.html')

if __name__ == '__main__':
    app.run(debug=True)