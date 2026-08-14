from .logic import CalculadorImpuestos
from ..models import LineaOrden, Orden


class OrdenBuilder:
    """
    Construye una Orden valida con Fluent Interface.
    El objeto solo se persiste en build() si pasa las reglas de negocio.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._evento = None
        self._plan = None

    def para_usuario(self, usuario):
        self._usuario = usuario
        return self

    def con_pase_de(self, evento):
        self._evento = evento
        self._plan = None
        return self

    def con_plan(self, plan):
        self._plan = plan
        self._evento = None
        return self

    def _validar(self):
        if not self._usuario:
            raise ValueError('La orden requiere un usuario.')

        if not self._evento and not self._plan:
            raise ValueError('Datos insuficientes para crear la orden.')

        if self._evento:
            if self._evento.ha_finalizado():
                raise ValueError('No se puede comprar un pase de un evento finalizado.')
            if self._evento.precio_pase <= 0:
                raise ValueError('El evento no tiene un pase de pago.')

        if self._plan and self._plan.es_gratuito():
            raise ValueError('El plan gratuito no genera cobro.')

    def build(self) -> Orden:
        self._validar()

        if self._evento:
            precio = self._evento.precio_pase
            concepto = 'pase'
            descripcion = f'Pase premium: {self._evento}'
        else:
            precio = self._plan.precio_mensual
            concepto = 'plan'
            descripcion = f'Suscripcion {self._plan.nombre}'

        total = CalculadorImpuestos.obtener_total_con_iva(precio)
        orden = Orden.objects.create(
            usuario=self._usuario,
            total=total,
        )
        LineaOrden.objects.create(
            orden=orden,
            concepto=concepto,
            descripcion=descripcion,
            precio_unitario=precio,
            cantidad=1,
            plan=self._plan,
            evento=self._evento,
        )
        self.reset()
        return orden
