"""Catalogo y acceso a mercados extraidos del monolito (lectura independiente)."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

# Semilla autonoma: el microservicio no depende del ORM de Django.
EVENTOS = {
    1: {
        'id': 1,
        'local': 'Atletico Nacional',
        'visitante': 'Millonarios',
        'competicion': 'Liga BetPlay',
        'deporte': 'futbol',
        'fase': 'Cuadrangulares',
        'sede': 'Medellin',
        'fecha': '2026-10-20T20:00:00-05:00',
        'estado': 'programado',
        'precio_pase': '12000.00',
        'mercados': [
            {'tipo': 'moneyline', 'es_premium': False},
            {'tipo': 'totales', 'es_premium': True},
            {'tipo': 'handicap', 'es_premium': True},
        ],
    },
    2: {
        'id': 2,
        'local': 'Lakers',
        'visitante': 'Celtics',
        'competicion': 'NBA',
        'deporte': 'baloncesto',
        'fase': 'Regular',
        'sede': 'Los Angeles',
        'fecha': '2026-10-21T22:00:00-05:00',
        'estado': 'programado',
        'precio_pase': '15000.00',
        'mercados': [
            {'tipo': 'moneyline', 'es_premium': False},
            {'tipo': 'totales', 'es_premium': True},
            {'tipo': 'handicap', 'es_premium': True},
        ],
    },
}

# Pases pagados en memoria (usuario -> set de evento_id).
_PASES: dict[str, set[int]] = {}


class ErrorValidacion(Exception):
    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class ErrorNoEncontrado(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


def listar_eventos():
    return [deepcopy(e) for e in EVENTOS.values()]


def obtener_evento(evento_id: int) -> dict:
    evento = EVENTOS.get(int(evento_id))
    if not evento:
        raise ErrorNoEncontrado('El evento no existe.')
    return deepcopy(evento)


def registrar_pase(usuario: str, evento_id: int) -> dict:
    evento = obtener_evento(evento_id)
    _PASES.setdefault(usuario, set()).add(int(evento_id))
    return {'usuario': usuario, 'evento_id': int(evento_id), 'pase': True, 'evento': evento}


def tiene_pase(usuario: str, evento_id: int) -> bool:
    return int(evento_id) in _PASES.get(usuario, set())


def mercados_para(usuario: str, evento_id: int) -> dict:
    evento = obtener_evento(evento_id)
    pase = tiene_pase(usuario, evento_id)
    mercados = []
    for m in evento['mercados']:
        visible = (not m['es_premium']) or pase
        mercados.append({
            'tipo': m['tipo'],
            'es_premium': m['es_premium'],
            'bloqueado': not visible,
            'etiqueta': 'premium' if m['es_premium'] else 'gratis',
        })
    return {
        'evento': evento,
        'usuario': usuario,
        'tiene_pase': pase,
        'mercados': mercados,
    }


def payload_integracion() -> dict:
    vigentes = [
        {
            'id': e['id'],
            'local': e['local'],
            'visitante': e['visitante'],
            'competicion': e['competicion'],
            'deporte': e['deporte'],
            'fecha': e['fecha'],
            'precio_pase': e['precio_pase'],
            'mercados_free': ['moneyline'],
        }
        for e in EVENTOS.values()
        if e['estado'] in {'programado', 'en_vivo'}
    ]
    return {
        'proyecto': 'Pronostix',
        'version_api': 'v2',
        'servicio': 'catalogo-flask',
        'equipo': ['Juan David Sierra', 'Juan José Palacio', 'Camilo Soto'],
        'descripcion': (
            'Catalogo estrangulado: eventos vigentes y mercados free '
            'expuestos como microservicio independiente.'
        ),
        'eventos': vigentes,
    }


def total_con_iva(precio) -> dict:
    try:
        base = Decimal(str(precio))
    except Exception as exc:  # noqa: BLE001
        raise ErrorValidacion('"precio" invalido.', 'precio') from exc
    total = (base * Decimal('1.19')).quantize(Decimal('0.01'))
    return {
        'precio': str(base),
        'iva': str(total - base),
        'total': str(total),
    }
