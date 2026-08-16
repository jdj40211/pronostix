from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .domain.acceso import AccesoMercado
from .domain.builders import OrdenBuilder
from .domain.modelo import MotorPronostico
from .models import Evento, ModeloPredictivo, Prediccion, Transaccion


def usuario_de(request):
    if request.user.is_authenticated:
        return request.user
    User = get_user_model()
    usuario, _ = User.objects.get_or_create(
        username='camilo_soto',
        defaults={'first_name': 'Camilo', 'last_name': 'Soto'},
    )
    return usuario


class CompraService:
    def __init__(self, pasarela):
        self.pasarela = pasarela
        self.builder = OrdenBuilder()

    def preparar(self, evento_id):
        evento = get_object_or_404(Evento, id=evento_id)
        return {'evento': evento}

    def crear(self, request, evento_id):
        evento = get_object_or_404(Evento, id=evento_id)
        contexto = {'evento': evento}
        try:
            orden = (
                self.builder
                .para_usuario(usuario_de(request))
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


class PrediccionService:
    def detalle(self, request, evento_id):
        evento = get_object_or_404(
            Evento.objects.select_related('local', 'visitante', 'competicion'),
            id=evento_id,
        )
        usuario = usuario_de(request)
        mercados = []
        for mercado in evento.mercados.all():
            visible = AccesoMercado.puede_ver(usuario, mercado)
            prediccion = mercado.prediccion_vigente()
            mercados.append({
                'mercado': mercado,
                'prediccion': prediccion if visible else None,
                'bloqueado': not visible,
            })
        return {'evento': evento, 'mercados': mercados}

    def generar_para(self, evento):
        deporte = evento.competicion.deporte
        modelo, _ = ModeloPredictivo.objects.get_or_create(
            version='v1-forma-reciente',
            deporte=deporte,
            defaults={'parametros': {'fuente': 'ratings_internos'}},
        )
        creadas = []
        for mercado in evento.mercados.all():
            probs = MotorPronostico.calcular_probabilidades(deporte, mercado.tipo)
            pred = Prediccion.objects.create(
                mercado=mercado,
                modelo=modelo,
                probabilidades=probs,
                valor_esperado=MotorPronostico.valor_esperado(probs),
                version_modelo=modelo.version,
            )
            creadas.append(pred)
        return creadas
