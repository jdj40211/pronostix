import logging
import os

import requests

logger = logging.getLogger(__name__)

# Contrato de respaldo si el aliado no esta configurado o no responde.
RESPALDO_ALIADO = {
    'proyecto': 'Equipo aliado (mock)',
    'version_api': 'v1',
    'disponible': False,
    'mensaje': (
        'Configure ALIADO_API_URL con el endpoint JSON del equipo aliado. '
        'Mientras tanto se muestra este contrato de ejemplo.'
    ),
    'items': [
        {'id': 1, 'titulo': 'Servicio demo del aliado', 'estado': 'disponible'},
        {'id': 2, 'titulo': 'Catalogo compartido', 'estado': 'pendiente'},
    ],
}


class ClienteAliado:
    """
    Consume el JSON del equipo aliado.
    Si falla la red o no hay URL, degrada al contrato de respaldo.
    """

    def __init__(self, url=None, timeout: float = 3.0):
        self.url = (url if url is not None else os.getenv('ALIADO_API_URL', '')).strip()
        self.timeout = timeout

    def obtener_resumen(self) -> dict:
        if not self.url:
            return dict(RESPALDO_ALIADO)

        try:
            respuesta = requests.get(self.url, timeout=self.timeout)
            respuesta.raise_for_status()
            datos = respuesta.json()
            if not isinstance(datos, dict):
                raise ValueError('La respuesta del aliado no es un objeto JSON.')
            datos = dict(datos)
            datos['disponible'] = True
            datos.setdefault('proyecto', 'Equipo aliado')
            return datos
        except Exception as exc:  # noqa: BLE001
            logger.warning('Aliado no disponible (%s): %s', self.url, exc)
            fallo = dict(RESPALDO_ALIADO)
            fallo['mensaje'] = f'Aliado no disponible: {exc}'
            return fallo
