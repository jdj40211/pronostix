from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    nombre = models.CharField(max_length=80)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    mercados_incluidos = models.CharField(max_length=200)
    limite_consultas_dia = models.PositiveIntegerField()

    def es_gratuito(self):
        return self.precio_mensual == 0

    def incluye_mercado(self, tipo):
        incluidos = self.mercados_incluidos.lower()
        if 'todos' in incluidos:
            return True
        return tipo.lower() in incluidos

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    ESTADOS = (
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
        ('vencida', 'Vencida'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    renovacion_auto = models.BooleanField(default=True)

    def esta_vigente(self):
        ahora = timezone.now()
        return self.estado == 'activa' and self.fecha_inicio <= ahora <= self.fecha_fin

    def cancelar(self):
        self.estado = 'cancelada'
        self.renovacion_auto = False
        self.save(update_fields=['estado', 'renovacion_auto'])

    def dias_restantes(self):
        if not self.esta_vigente():
            return 0
        return (self.fecha_fin - timezone.now()).days

    def __str__(self):
        return f'{self.usuario} - {self.plan} ({self.estado})'


class Competicion(models.Model):
    nombre = models.CharField(max_length=120)
    deporte = models.CharField(max_length=80)
    temporada = models.CharField(max_length=20)
    pais = models.CharField(max_length=80)

    def __str__(self):
        return f'{self.nombre} ({self.deporte})'


class Equipo(models.Model):
    nombre = models.CharField(max_length=120)
    pais = models.CharField(max_length=80)
    deporte = models.CharField(max_length=80)
    ranking = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    ESTADOS = (
        ('programado', 'Programado'),
        ('en_vivo', 'En vivo'),
        ('finalizado', 'Finalizado'),
    )

    competicion = models.ForeignKey(
        Competicion, on_delete=models.CASCADE, related_name='eventos',
    )
    local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='como_local')
    visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='como_visitante')
    fecha = models.DateTimeField()
    fase = models.CharField(max_length=80)
    sede = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programado')
    es_premium = models.BooleanField(default=True)
    precio_pase = models.DecimalField(max_digits=10, decimal_places=2)

    def ha_finalizado(self):
        return self.estado == 'finalizado'

    def esta_en_vivo(self):
        return self.estado == 'en_vivo'

    def __str__(self):
        return f'{self.local} vs {self.visitante}'


class Orden(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('reembolsada', 'Reembolsada'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    moneda = models.CharField(max_length=3, default='COP')
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def confirmar_pago(self):
        self.estado = 'pagada'
        self.save(update_fields=['estado'])

    def esta_pagada(self):
        return self.estado == 'pagada'

    def __str__(self):
        return f'Orden {self.id} ({self.estado})'


class LineaOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='lineas')
    concepto = models.CharField(max_length=40)
    descripcion = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)
    plan = models.ForeignKey(Plan, null=True, blank=True, on_delete=models.SET_NULL)
    evento = models.ForeignKey(Evento, null=True, blank=True, on_delete=models.SET_NULL)

    def subtotal(self):
        return self.precio_unitario * self.cantidad


class Transaccion(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    )

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='transacciones')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='COP')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    referencia = models.CharField(max_length=80, blank=True)
    fecha_procesado = models.DateTimeField(null=True, blank=True)

    def aprobar(self, referencia=''):
        self.estado = 'aprobada'
        self.referencia = referencia or self.referencia
        self.fecha_procesado = timezone.now()
        self.save(update_fields=['estado', 'referencia', 'fecha_procesado'])

    def rechazar(self, motivo=''):
        self.estado = 'rechazada'
        self.referencia = motivo
        self.fecha_procesado = timezone.now()
        self.save(update_fields=['estado', 'referencia', 'fecha_procesado'])

    def esta_aprobada(self):
        return self.estado == 'aprobada'


class ModeloPredictivo(models.Model):
    version = models.CharField(max_length=40)
    deporte = models.CharField(max_length=80)
    parametros = models.JSONField(default=dict, blank=True)
    fecha_calibracion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.deporte} {self.version}'


class Mercado(models.Model):
    TIPOS = (
        ('moneyline', 'Resultado / moneyline'),
        ('totales', 'Totales over-under'),
        ('handicap', 'Handicap'),
        ('anotadores', 'Anotadores'),
    )

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='mercados')
    tipo = models.CharField(max_length=40, choices=TIPOS)
    es_premium = models.BooleanField(default=False)

    def prediccion_vigente(self):
        return self.predicciones.order_by('-fecha_calculo').first()

    def __str__(self):
        return f'{self.evento} - {self.tipo}'


class Prediccion(models.Model):
    mercado = models.ForeignKey(Mercado, on_delete=models.CASCADE, related_name='predicciones')
    modelo = models.ForeignKey(ModeloPredictivo, on_delete=models.CASCADE, related_name='predicciones')
    probabilidades = models.JSONField()
    valor_esperado = models.FloatField(default=0)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    version_modelo = models.CharField(max_length=40)

    def mas_probable(self):
        if not self.probabilidades:
            return None
        return max(self.probabilidades, key=self.probabilidades.get)

    def probabilidad_de(self, opcion):
        return self.probabilidades.get(opcion)

    def __str__(self):
        return f'{self.mercado.tipo} {self.version_modelo}'
