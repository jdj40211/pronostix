from django.contrib.auth import get_user_model

from .domain.acceso import AccesoMercado
from .domain.builders import OrdenBuilder
from .domain.exceptions import ConflictoNegocio, EventoNoEncontrado
from .domain.modelo import MotorPronostico
from .models import Evento, LineaOrden, ModeloPredictivo, Prediccion, Transaccion


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
        return {'evento': self._evento(evento_id)}

    def _evento(self, evento_id):
        try:
            return Evento.objects.select_related('local', 'visitante', 'competicion').get(id=evento_id)
        except Evento.DoesNotExist as exc:
            raise EventoNoEncontrado('El evento no existe.') from exc

    def crear_api(self, request, evento_id):
        evento = self._evento(evento_id)

        usuario = usuario_de(request)
        ya_pagado = LineaOrden.objects.filter(
            evento=evento,
            concepto='pase',
            orden__usuario=usuario,
            orden__estado='pagada',
        ).exists()
        if ya_pagado:
            raise ConflictoNegocio('Ya existe un pase pagado para este evento.')

        try:
            orden = (
                self.builder
                .para_usuario(usuario)
                .con_pase_de(evento)
                .build()
            )
        except ValueError as exc:
            raise ConflictoNegocio(str(exc)) from exc

        transaccion = Transaccion.objects.create(
            orden=orden,
            monto=orden.total,
            moneda=orden.moneda,
        )
        if not self.pasarela.procesar(transaccion):
            orden.delete()
            raise ValueError('La pasarela rechazo el pago.')
        orden.confirmar_pago()
        return {'orden': orden, 'transaccion': transaccion, 'evento': evento}

    def crear(self, request, evento_id):
        evento = self._evento(evento_id)
        contexto = {'evento': evento}
        try:
            resultado = self.crear_api(request, evento_id)
            contexto['orden'] = resultado['orden']
            contexto['transaccion'] = resultado['transaccion']
            contexto['mensaje_exito'] = (
                f'Orden {resultado["orden"].id} pagada. Total ${resultado["orden"].total}. '
                f'Ref {resultado["transaccion"].referencia}.'
            )
        except ConflictoNegocio as exc:
            contexto['error'] = str(exc)
            contexto['conflicto'] = True
        except (KeyError, ValueError) as exc:
            contexto['error'] = str(exc) if str(exc) else 'No se pudo completar la compra.'
        return contexto


class CatalogoService:
    def listar(self):
        return Evento.objects.select_related('local', 'visitante', 'competicion')


class PrediccionService:
    def detalle(self, request, evento_id):
        try:
            evento = Evento.objects.select_related('local', 'visitante', 'competicion').get(id=evento_id)
        except Evento.DoesNotExist as exc:
            raise EventoNoEncontrado('El evento no existe.') from exc
        usuario = usuario_de(request)
        mercados = []
        for mercado in evento.mercados.all():
            visible = AccesoMercado.puede_ver(usuario, mercado)
            prediccion = AccesoMercado.prediccion_vigente(mercado) if visible else None
            mercados.append({
                'mercado': mercado,
                'prediccion': prediccion,
                'mas_probable': MotorPronostico.mas_probable(prediccion.probabilidades) if prediccion else None,
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
