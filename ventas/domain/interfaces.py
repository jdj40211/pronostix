from abc import ABC, abstractmethod


class PasarelaPago(ABC):
    """
    DIP: el dominio depende de esta abstraccion, no de un banco concreto.
    La pasarela propia autoriza, captura y evalua riesgo.
    """

    @abstractmethod
    def procesar(self, transaccion) -> bool:
        pass
