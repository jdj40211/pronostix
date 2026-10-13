import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from motor import ErrorValidacion, pronosticar

SERVICIO = 'pronosticos-flask'

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
logger = logging.getLogger(SERVICIO)


def error(status, codigo, mensaje, campo=None):
    cuerpo = {'error': {'codigo': codigo, 'mensaje': mensaje}, 'servicio': SERVICIO}
    if campo:
        cuerpo['error']['campo'] = campo
    return jsonify(cuerpo), status


@app.get('/api/v2/pronosticos/salud')
def salud():
    return jsonify({'estado': 'ok', 'servicio': SERVICIO})


@app.post('/api/v2/pronosticos/', strict_slashes=False)
def calcular_pronosticos():
    if not request.is_json:
        return error(400, 'contenido_invalido', 'Envie Content-Type: application/json.')
    datos = request.get_json(silent=True)
    if datos is None:
        return error(400, 'json_invalido', 'El cuerpo no es un JSON valido.')

    resultado = pronosticar(datos)
    return jsonify({'servicio': SERVICIO, 'version_api': 'v2', **resultado}), 200


@app.errorhandler(ErrorValidacion)
def manejar_validacion(exc):
    return error(400, 'validacion', exc.mensaje, exc.campo)


@app.errorhandler(HTTPException)
def manejar_http(exc):
    return error(exc.code, exc.name.lower().replace(' ', '_'), exc.description)


@app.errorhandler(Exception)
def manejar_inesperado(exc):
    logger.exception('Error no controlado en el motor de pronosticos')
    return error(500, 'error_interno', 'El motor de pronosticos fallo. Intente de nuevo.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
