"""Clientes HTTP hacia los microservicios Flask (Strangler >70%)."""

from __future__ import annotations

import logging
import os

import requests

from ventas.domain.interfaces import PasarelaPago, ProveedorEstadisticas

logger = logging.getLogger(__name__)


def _url(var_name: str, default: str = '') -> str:
    return (os.getenv(var_name) or default).rstrip('/')


class HttpPasarela(PasarelaPago):
    """DIP: el dominio sigue hablando con PasarelaPago; la impl. es el MS de pagos."""

    def __init__(self, base_url=None, modo=None, timeout: float = 5.0):
        self.base_url = (base_url or _url('PAGOS_URL')).rstrip('/')
        self.modo = (modo or os.getenv('ENV_TYPE', 'REAL')).upper()
        self.timeout = timeout

    def procesar(self, transaccion) -> bool:
        if not self.base_url:
            raise RuntimeError('PAGOS_URL no configurada para HttpPasarela.')
        try:
            respuesta = requests.post(
                f'{self.base_url}/api/v2/pagos/',
                json={
                    'orden_id': transaccion.orden_id,
                    'monto': str(transaccion.monto),
                    'moneda': getattr(transaccion, 'moneda', 'COP'),
                    'modo': self.modo,
                },
                timeout=self.timeout,
            )
            datos = respuesta.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning('MS pagos no disponible: %s', exc)
            transaccion.rechazar(motivo='Microservicio de pagos no disponible')
            return False

        if datos.get('aprobado'):
            transaccion.aprobar(referencia=datos.get('referencia') or 'MS-OK')
            return True
        transaccion.rechazar(motivo=datos.get('motivo') or 'Rechazado por MS pagos')
        return False


class HttpEstadisticas(ProveedorEstadisticas):
    def __init__(self, base_url=None, timeout: float = 4.0):
        self.base_url = (base_url or _url('ESTADISTICAS_URL')).rstrip('/')
        self.timeout = timeout

    def forma_reciente(self, local: str, visitante: str, deporte: str) -> dict:
        if not self.base_url:
            return {
                'fuente': 'http-estadisticas',
                'disponible': False,
                'local': local,
                'visitante': visitante,
                'deporte': deporte,
                'resumen': 'ESTADISTICAS_URL no configurada.',
                'detalle': {},
            }
        try:
            respuesta = requests.post(
                f'{self.base_url}/api/v2/estadisticas/forma/',
                json={'local': local, 'visitante': visitante, 'deporte': deporte},
                timeout=self.timeout,
            )
            respuesta.raise_for_status()
            return respuesta.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning('MS estadisticas no disponible: %s', exc)
            return {
                'fuente': 'http-estadisticas',
                'disponible': False,
                'local': local,
                'visitante': visitante,
                'deporte': deporte,
                'resumen': 'Estadisticas del microservicio no disponibles.',
                'detalle': {'error': str(exc)},
            }


class ClienteCatalogoMS:
    def __init__(self, base_url=None, timeout: float = 4.0):
        self.base_url = (base_url or _url('CATALOGO_URL')).rstrip('/')
        self.timeout = timeout

    def disponible(self) -> bool:
        return bool(self.base_url)

    def integracion(self) -> dict | None:
        if not self.base_url:
            return None
        try:
            r = requests.get(
                f'{self.base_url}/api/v2/catalogo/integracion/',
                timeout=self.timeout,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning('MS catalogo no disponible: %s', exc)
            return None

    def sincronizar_pase(self, usuario: str, evento_id: int) -> bool:
        if not self.base_url:
            return False
        try:
            r = requests.post(
                f'{self.base_url}/api/v2/catalogo/pases/',
                json={'usuario': usuario, 'evento_id': evento_id},
                timeout=self.timeout,
            )
            return r.status_code in {200, 201}
        except Exception as exc:  # noqa: BLE001
            logger.warning('No se pudo sincronizar pase con catalogo: %s', exc)
            return False
