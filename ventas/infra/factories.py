import os

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
