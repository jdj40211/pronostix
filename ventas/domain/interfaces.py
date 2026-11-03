from abc import ABC, abstractmethod


class PasarelaPago(ABC):
    """
    DIP: el dominio depende de esta abstraccion, no de un banco concreto.
    La pasarela propia autoriza, captura y evalua riesgo.
    """

    @abstractmethod
    def procesar(self, transaccion) -> bool:
        pass


class ProveedorEstadisticas(ABC):
    """
    Adapter: el dominio pide forma reciente sin conocer el proveedor HTTP.
    """

    @abstractmethod
    def forma_reciente(self, local: str, visitante: str, deporte: str) -> dict:
        """
        Devuelve un dict con fuente, local, visitante y resumen legible.
        Nunca debe lanzar: ante fallo, devolver un degradado explicito.
        """
