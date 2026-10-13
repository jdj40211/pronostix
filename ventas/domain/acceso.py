from django.utils import timezone

from .logic import ReglasPlan
from ..models import LineaOrden, Prediccion, Suscripcion


class AccesoMercado:
    """
    DIP/SRP: el derecho de uso vive aqui, no en la vista.
    Un mercado free se ve siempre; el premium pide pase del evento o plan vigente.
    """

    @staticmethod
    def _pases_pagados(usuario):
        return LineaOrden.objects.filter(
            concepto='pase',
            orden__usuario=usuario,
            orden__estado='pagada',
        )

    @classmethod
    def tiene_pase(cls, usuario, evento):
        if usuario is None:
            return False
        return cls._pases_pagados(usuario).filter(evento=evento).exists()

    @classmethod
    def eventos_con_pase(cls, usuario):
        if usuario is None:
            return set()
        return set(cls._pases_pagados(usuario).values_list('evento_id', flat=True))

    @classmethod
    def puede_ver(cls, usuario, mercado):
        if not mercado.es_premium:
            return True
        if usuario is None:
            return False

        if cls.tiene_pase(usuario, mercado.evento):
            return True

        ahora = timezone.now()
        vigentes = Suscripcion.objects.filter(
            usuario=usuario,
            estado='activa',
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
        ).select_related('plan')
        return any(ReglasPlan.incluye_mercado(sub.plan, mercado.tipo) for sub in vigentes)

    @staticmethod
    def prediccion_vigente(mercado):
        return Prediccion.objects.filter(mercado=mercado).order_by('-fecha_calculo').first()
