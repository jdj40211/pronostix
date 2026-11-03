from django.contrib.auth import get_user_model

from .domain.acceso import AccesoMercado
from .domain.builders import OrdenBuilder
from .domain.exceptions import ConflictoNegocio, EventoNoEncontrado
from .domain.logic import CalculadorImpuestos
from .domain.modelo import MotorPronostico
from .infra.aliado import ClienteAliado
from .infra.factories import EstadisticasFactory
from .infra.http_clients import ClienteCatalogoMS
from .models import Evento, ModeloPredictivo, Prediccion, Transaccion
from .tasks import notificar_compra_pase


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

    def preparar(self, request, evento_id):
        evento = self._evento(evento_id)
        total = CalculadorImpuestos.obtener_total_con_iva(evento.precio_pase)
        return {
            'evento': evento,
            'iva': total - evento.precio_pase,
            'total': total,
            'tiene_pase': AccesoMercado.tiene_pase(usuario_de(request), evento),
        }

    def _evento(self, evento_id):
        try:
            return Evento.objects.select_related('local', 'visitante', 'competicion').get(id=evento_id)
        except Evento.DoesNotExist as exc:
            raise EventoNoEncontrado('El evento no existe.') from exc

    def crear_api(self, request, evento_id):
        evento = self._evento(evento_id)

        usuario = usuario_de(request)
        if AccesoMercado.tiene_pase(usuario, evento):
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
        # Sincroniza el pase con el microservicio de catalogo (mejor esfuerzo).
        ClienteCatalogoMS().sincronizar_pase(usuario.username, evento.id)
        notificar_compra_pase.delay(
            orden_id=orden.id,
            evento_id=evento.id,
            usuario=usuario.username,
            total=str(orden.total),
            referencia=transaccion.referencia,
        )
        return {'orden': orden, 'transaccion': transaccion, 'evento': evento}

    def crear(self, request, evento_id):
        contexto = self.preparar(request, evento_id)
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

    def portada(self, request):
        return {
            'eventos': self.listar(),
            'eventos_con_pase': AccesoMercado.eventos_con_pase(usuario_de(request)),
            'aliado': ClienteAliado().obtener_resumen(),
        }

    def payload_integracion(self):
        """JSON estable: prefiere el MS de catalogo; si no, el monolito."""
        remoto = ClienteCatalogoMS().integracion()
        if remoto:
            remoto = dict(remoto)
            remoto['origen'] = 'microservicio_catalogo'
            return remoto

        eventos = []
        for evento in self.listar().filter(estado__in=['programado', 'en_vivo']):
            eventos.append({
                'id': evento.id,
                'local': str(evento.local),
                'visitante': str(evento.visitante),
                'competicion': str(evento.competicion),
                'deporte': evento.competicion.deporte,
                'fecha': evento.fecha.isoformat(),
                'precio_pase': str(evento.precio_pase),
                'mercados_free': ['moneyline'],
            })
        return {
            'proyecto': 'Pronostix',
            'version_api': 'v1',
            'origen': 'monolito_django',
            'equipo': ['Juan David Sierra', 'Juan José Palacio', 'Camilo Soto'],
            'descripcion': (
                'Proyecciones estadisticas para apuestas deportivas. '
                'Expone eventos vigentes y mercados free.'
            ),
            'eventos': eventos,
        }


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
        proveedor = EstadisticasFactory.get_proveedor()
        forma = proveedor.forma_reciente(
            str(evento.local),
            str(evento.visitante),
            evento.competicion.deporte,
        )
        return {
            'evento': evento,
            'mercados': mercados,
            'tiene_pase': AccesoMercado.tiene_pase(usuario, evento),
            'forma_externa': forma,
        }

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
