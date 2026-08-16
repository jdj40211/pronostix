from django.utils import timezone

from ..models import LineaOrden, Suscripcion


class AccesoMercado:
    """
    DIP/SRP: el derecho de uso vive aqui, no en la vista.
    Un mercado free se ve siempre; el premium pide pase del evento o plan vigente.
    """

    @staticmethod
    def puede_ver(usuario, mercado):
        if not mercado.es_premium:
            return True
        if usuario is None:
            return False

        tiene_pase = LineaOrden.objects.filter(
            evento=mercado.evento,
            concepto='pase',
            orden__usuario=usuario,
            orden__estado='pagada',
        ).exists()
        if tiene_pase:
            return True

        ahora = timezone.now()
        vigentes = Suscripcion.objects.filter(
            usuario=usuario,
            estado='activa',
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
        ).select_related('plan')
        return any(sub.plan.incluye_mercado(mercado.tipo) for sub in vigentes)
