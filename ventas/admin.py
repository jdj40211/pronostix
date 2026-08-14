from django.contrib import admin

from .models import Competicion, Equipo, Evento, LineaOrden, Orden, Plan, Transaccion


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_mensual', 'limite_consultas_dia')


@admin.register(Competicion)
class CompeticionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'deporte', 'temporada', 'pais')


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'deporte', 'pais')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'local', 'visitante', 'fecha', 'es_premium', 'precio_pase', 'estado')


class LineaInline(admin.TabularInline):
    model = LineaOrden
    extra = 0


class TxInline(admin.TabularInline):
    model = Transaccion
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'total', 'estado', 'fecha_creacion')
    inlines = [LineaInline, TxInline]
