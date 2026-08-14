from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .domain.builders import OrdenBuilder
from .models import Evento, Transaccion


class CompraService:
    def __init__(self, pasarela):
        self.pasarela = pasarela
        self.builder = OrdenBuilder()

    def _usuario(self, request):
        if request.user.is_authenticated:
            return request.user
        User = get_user_model()
        usuario, _ = User.objects.get_or_create(
            username='camilo_soto',
            defaults={'first_name': 'Camilo', 'last_name': 'Soto'},
        )
        return usuario

    def preparar(self, evento_id):
        evento = get_object_or_404(Evento, id=evento_id)
        return {'evento': evento}

    def crear(self, request, evento_id):
        evento = get_object_or_404(Evento, id=evento_id)
        contexto = {'evento': evento}
        try:
            orden = (
                self.builder
                .para_usuario(self._usuario(request))
                .con_pase_de(evento)
                .build()
            )
            transaccion = Transaccion.objects.create(
                orden=orden,
                monto=orden.total,
                moneda=orden.moneda,
            )
            if not self.pasarela.procesar(transaccion):
                orden.delete()
                raise ValueError('La pasarela rechazo el pago.')
            orden.confirmar_pago()
            contexto['orden'] = orden
            contexto['transaccion'] = transaccion
            contexto['mensaje_exito'] = (
                f'Orden {orden.id} pagada. Total ${orden.total}. '
                f'Ref {transaccion.referencia}.'
            )
        except (KeyError, ValueError) as exc:
            contexto['error'] = str(exc) if str(exc) else 'No se pudo completar la compra.'
        return contexto
