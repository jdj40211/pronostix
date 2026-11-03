import os

from django.conf import settings

from .estadisticas import MockEstadisticas, TheSportsDbAdapter
from .gateways import MockPasarela, PasarelaPronostix


class PasarelaFactory:
    """
    Factory Method: la vista y el servicio no deciden que pasarela crear.
    El comportamiento cambia con ENV_TYPE=MOCK o ENV_TYPE=REAL.
    """

    @staticmethod
    def get_pasarela():
        env_type = os.getenv('ENV_TYPE', 'REAL').upper()
        if env_type == 'MOCK':
            return MockPasarela()
        return PasarelaPronostix()


class EstadisticasFactory:
    """
    Elige el Adapter de estadisticas externas segun STATS_PROVIDER.
    MOCK: datos locales. REAL: TheSportsDB (API de terceros).
    """

    @staticmethod
    def get_proveedor():
        proveedor = os.getenv(
            'STATS_PROVIDER',
            getattr(settings, 'STATS_PROVIDER', 'MOCK'),
        ).upper()
        if proveedor == 'REAL':
            return TheSportsDbAdapter(
                api_key=getattr(settings, 'THESPORTSDB_API_KEY', '123'),
            )
        return MockEstadisticas()
