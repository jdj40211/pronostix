from decimal import Decimal, ROUND_HALF_UP


class CalculadorImpuestos:
    """
    SRP: solo calcula impuestos.
    OCP: se puede extender (otro pais, otro IVA) sin tocar el Builder.
    """

    IVA = Decimal('1.19')

    @classmethod
    def obtener_total_con_iva(cls, precio_base):
        total = Decimal(str(precio_base)) * cls.IVA
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class ReglasPlan:
    @staticmethod
    def es_gratuito(plan):
        return plan.precio_mensual == 0

    @staticmethod
    def incluye_mercado(plan, tipo):
        incluidos = plan.mercados_incluidos.lower()
        if 'todos' in incluidos:
            return True
        return tipo.lower() in incluidos


class ReglasEvento:
    @staticmethod
    def ha_finalizado(evento):
        return evento.estado == 'finalizado'
