import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from dominio import (
    ErrorNoEncontrado,
    ErrorValidacion,
    listar_eventos,
    mercados_para,
    obtener_evento,
    payload_integracion,
    registrar_pase,
    total_con_iva,
)

SERVICIO = 'catalogo-flask'

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
logger = logging.getLogger(SERVICIO)


def error(status, codigo, mensaje, campo=None):
    cuerpo = {'error': {'codigo': codigo, 'mensaje': mensaje}, 'servicio': SERVICIO}
    if campo:
        cuerpo['error']['campo'] = campo
    return jsonify(cuerpo), status


@app.get('/api/v2/catalogo/salud')
def salud():
    return jsonify({'estado': 'ok', 'servicio': SERVICIO})


@app.get('/api/v2/catalogo/eventos/', strict_slashes=False)
def eventos():
    return jsonify({
        'servicio': SERVICIO,
        'version_api': 'v2',
        'eventos': listar_eventos(),
    })


@app.get('/api/v2/catalogo/eventos/<int:evento_id>', strict_slashes=False)
def evento_detalle(evento_id):
    evento = obtener_evento(evento_id)
    return jsonify({'servicio': SERVICIO, 'version_api': 'v2', 'evento': evento})


@app.get('/api/v2/catalogo/eventos/<int:evento_id>/mercados', strict_slashes=False)
def evento_mercados(evento_id):
    usuario = request.args.get('usuario') or 'anonimo'
    return jsonify({
        'servicio': SERVICIO,
        'version_api': 'v2',
        **mercados_para(usuario, evento_id),
    })


@app.post('/api/v2/catalogo/pases/', strict_slashes=False)
def crear_pase():
    if not request.is_json:
        return error(400, 'contenido_invalido', 'Envie Content-Type: application/json.')
    datos = request.get_json(silent=True) or {}
    usuario = datos.get('usuario')
    evento_id = datos.get('evento_id')
    if not usuario:
        return error(400, 'validacion', '"usuario" es obligatorio.', 'usuario')
    if not evento_id:
        return error(400, 'validacion', '"evento_id" es obligatorio.', 'evento_id')
    return jsonify({
        'servicio': SERVICIO,
        'version_api': 'v2',
        **registrar_pase(str(usuario), int(evento_id)),
    }), 201


@app.get('/api/v2/catalogo/integracion/', strict_slashes=False)
def integracion():
    return jsonify(payload_integracion())


@app.post('/api/v2/catalogo/iva/', strict_slashes=False)
def iva():
    if not request.is_json:
        return error(400, 'contenido_invalido', 'Envie Content-Type: application/json.')
    datos = request.get_json(silent=True) or {}
    return jsonify({
        'servicio': SERVICIO,
        'version_api': 'v2',
        **total_con_iva(datos.get('precio')),
    })


@app.errorhandler(ErrorValidacion)
def manejar_validacion(exc):
    return error(400, 'validacion', exc.mensaje, exc.campo)


@app.errorhandler(ErrorNoEncontrado)
def manejar_404(exc):
    return error(404, 'no_encontrado', exc.mensaje)


@app.errorhandler(HTTPException)
def manejar_http(exc):
    return error(exc.code, exc.name.lower().replace(' ', '_'), exc.description)


@app.errorhandler(Exception)
def manejar_inesperado(exc):
    logger.exception('Error no controlado en catalogo')
    return error(500, 'error_interno', 'El servicio de catalogo fallo. Intente de nuevo.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
