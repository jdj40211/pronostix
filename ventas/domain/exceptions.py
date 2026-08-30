class EventoNoEncontrado(Exception):
    pass


class ConflictoNegocio(Exception):
    """409: el estado actual impide completar el caso de uso."""
