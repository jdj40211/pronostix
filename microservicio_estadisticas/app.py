import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from adapter import get_proveedor

SERVICIO = 'estadisticas-flask'

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
logger = logging.getLogger(SERVICIO)


def error(status, codigo, mensaje, campo=None):
    cuerpo = {'error': {'codigo': codigo, 'mensaje': mensaje}, 'servicio': SERVICIO}
    if campo:
        cuerpo['error']['campo'] = campo
    return jsonify(cuerpo), status


@app.get('/api/v2/estadisticas/salud')
def salud():
    return jsonify({'estado': 'ok', 'servicio': SERVICIO})


@app.post('/api/v2/estadisticas/forma/', strict_slashes=False)
def forma():
    if not request.is_json:
        return error(400, 'contenido_invalido', 'Envie Content-Type: application/json.')
    datos = request.get_json(silent=True)
    if datos is None:
        return error(400, 'json_invalido', 'El cuerpo no es un JSON valido.')
    local = datos.get('local')
    visitante = datos.get('visitante')
    deporte = datos.get('deporte') or 'futbol'
    if not local or not visitante:
        return error(400, 'validacion', '"local" y "visitante" son obligatorios.')
    forma_data = get_proveedor().forma_reciente(str(local), str(visitante), str(deporte))
    return jsonify({'servicio': SERVICIO, 'version_api': 'v2', **forma_data})


@app.errorhandler(HTTPException)
def manejar_http(exc):
    return error(exc.code, exc.name.lower().replace(' ', '_'), exc.description)


@app.errorhandler(Exception)
def manejar_inesperado(exc):
    logger.exception('Error no controlado en estadisticas')
    return error(500, 'error_interno', 'El servicio de estadisticas fallo.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
