"""Adapter de estadisticas externas (DIP) como microservicio independiente."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class ProveedorEstadisticas(ABC):
    @abstractmethod
    def forma_reciente(self, local: str, visitante: str, deporte: str) -> dict:
        raise NotImplementedError


class MockEstadisticas(ProveedorEstadisticas):
    def forma_reciente(self, local: str, visitante: str, deporte: str) -> dict:
        return {
            'fuente': 'mock-interno',
            'disponible': True,
            'local': local,
            'visitante': visitante,
            'deporte': deporte,
            'resumen': f'{local}: W-W-D-L-W · {visitante}: D-W-L-W-D',
            'detalle': {
                'local_ultimos': ['W', 'W', 'D', 'L', 'W'],
                'visitante_ultimos': ['D', 'W', 'L', 'W', 'D'],
            },
        }


class TheSportsDbAdapter(ProveedorEstadisticas):
    BASE = 'https://www.thesportsdb.com/api/v1/json'

    def __init__(self, api_key: str = '123', timeout: float = 4.0):
        self.api_key = api_key or '123'
        self.timeout = timeout

    def forma_reciente(self, local: str, visitante: str, deporte: str) -> dict:
        try:
            local_info = self._buscar_equipo(local)
            visitante_info = self._buscar_equipo(visitante)
            return {
                'fuente': 'thesportsdb',
                'disponible': True,
                'local': local,
                'visitante': visitante,
                'deporte': deporte,
                'resumen': (
                    f"{local}: {local_info.get('strStadium', 'estadio n/d')} · "
                    f"{visitante}: {visitante_info.get('strStadium', 'estadio n/d')}"
                ),
                'detalle': {
                    'local_liga': local_info.get('strLeague') or 'n/d',
                    'visitante_liga': visitante_info.get('strLeague') or 'n/d',
                },
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning('TheSportsDB fallo: %s', exc)
            return {
                'fuente': 'thesportsdb',
                'disponible': False,
                'local': local,
                'visitante': visitante,
                'deporte': deporte,
                'resumen': 'Estadisticas externas no disponibles en este momento.',
                'detalle': {'error': str(exc)},
            }

    def _buscar_equipo(self, nombre: str) -> dict:
        url = f'{self.BASE}/{self.api_key}/searchteams.php'
        respuesta = requests.get(url, params={'t': nombre}, timeout=self.timeout)
        respuesta.raise_for_status()
        equipos = (respuesta.json() or {}).get('teams') or []
        return equipos[0] if equipos else {'strTeam': nombre}


def get_proveedor() -> ProveedorEstadisticas:
    if os.getenv('STATS_PROVIDER', 'MOCK').upper() == 'REAL':
        return TheSportsDbAdapter(api_key=os.getenv('THESPORTSDB_API_KEY', '123'))
    return MockEstadisticas()
