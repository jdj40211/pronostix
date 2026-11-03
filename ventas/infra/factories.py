import os

from django.conf import settings

from .estadisticas import MockEstadisticas, TheSportsDbAdapter
from .gateways import MockPasarela, PasarelaPronostix
from .http_clients import HttpEstadisticas, HttpPasarela


class PasarelaFactory:
    """
    Factory Method: si PAGOS_URL esta definida, el cobro va al microservicio Flask.
    Si no, usa las implementaciones locales (tests / runserver sin Docker).
    """

    @staticmethod
    def get_pasarela():
        pagos_url = os.getenv('PAGOS_URL', getattr(settings, 'PAGOS_URL', '')).strip()
        env_type = os.getenv('ENV_TYPE', 'REAL').upper()
        if pagos_url:
            return HttpPasarela(base_url=pagos_url, modo=env_type)
        if env_type == 'MOCK':
            return MockPasarela()
        return PasarelaPronostix()


class EstadisticasFactory:
    """
    Si ESTADISTICAS_URL esta definida, consulta el microservicio.
    Si no, Adapter local MOCK/REAL (TheSportsDB).
    """

    @staticmethod
    def get_proveedor():
        url = os.getenv(
            'ESTADISTICAS_URL',
            getattr(settings, 'ESTADISTICAS_URL', ''),
        ).strip()
        if url:
            return HttpEstadisticas(base_url=url)

        proveedor = os.getenv(
            'STATS_PROVIDER',
            getattr(settings, 'STATS_PROVIDER', 'MOCK'),
        ).upper()
        if proveedor == 'REAL':
            return TheSportsDbAdapter(
                api_key=getattr(settings, 'THESPORTSDB_API_KEY', '123'),
            )
        return MockEstadisticas()
