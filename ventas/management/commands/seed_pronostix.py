from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ventas.models import Competicion, Equipo, Evento, Mercado, Plan, Prediccion
from ventas.services import PrediccionService


class Command(BaseCommand):
    help = 'Crea planes, equipos y eventos de prueba para Pronostix.'

    def handle(self, *args, **options):
        planes = [
            ('Free', 0, 'moneyline', 5),
            ('Premium', 39000, 'moneyline, totales, handicap', 50),
            ('Pro', 79000, 'todos los mercados + anotadores', 200),
        ]
        for nombre, precio, mercados, limite in planes:
            Plan.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'precio_mensual': precio,
                    'mercados_incluidos': mercados,
                    'limite_consultas_dia': limite,
                },
            )

        liga, _ = Competicion.objects.get_or_create(
            nombre='Liga BetPlay',
            defaults={'deporte': 'futbol', 'temporada': '2026-1', 'pais': 'Colombia'},
        )
        nba, _ = Competicion.objects.get_or_create(
            nombre='NBA',
            defaults={'deporte': 'basquetbol', 'temporada': '2025-26', 'pais': 'USA'},
        )

        nacional, _ = Equipo.objects.get_or_create(
            nombre='Atletico Nacional', defaults={'pais': 'Colombia', 'deporte': 'futbol'},
        )
        millonarios, _ = Equipo.objects.get_or_create(
            nombre='Millonarios', defaults={'pais': 'Colombia', 'deporte': 'futbol'},
        )
        lakers, _ = Equipo.objects.get_or_create(
            nombre='Lakers', defaults={'pais': 'USA', 'deporte': 'basquetbol'},
        )
        celtics, _ = Equipo.objects.get_or_create(
            nombre='Celtics', defaults={'pais': 'USA', 'deporte': 'basquetbol'},
        )

        ahora = timezone.now() + timedelta(days=3)
        Evento.objects.get_or_create(
            competicion=liga,
            local=nacional,
            visitante=millonarios,
            defaults={
                'fecha': ahora,
                'fase': 'Cuadrangulares',
                'sede': 'Atanasio Girardot',
                'es_premium': True,
                'precio_pase': 12000,
            },
        )
        Evento.objects.get_or_create(
            competicion=nba,
            local=lakers,
            visitante=celtics,
            defaults={
                'fecha': ahora + timedelta(days=1),
                'fase': 'Regular season',
                'sede': 'Crypto.com Arena',
                'es_premium': True,
                'precio_pase': 18000,
            },
        )
        self.stdout.write(self.style.SUCCESS('Planes y eventos listos.'))
        self._sembrar_mercados()

    def _sembrar_mercados(self):
        tipos = [
            ('moneyline', False),
            ('totales', True),
            ('handicap', True),
        ]
        for evento in Evento.objects.select_related('competicion'):
            for tipo, premium in tipos:
                Mercado.objects.get_or_create(
                    evento=evento,
                    tipo=tipo,
                    defaults={'es_premium': premium},
                )
            if not Prediccion.objects.filter(mercado__evento=evento).exists():
                PrediccionService().generar_para(evento)
        self.stdout.write(self.style.SUCCESS('Mercados y predicciones listos.'))
