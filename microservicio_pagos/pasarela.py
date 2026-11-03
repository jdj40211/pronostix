"""Logica de cobro extraida del monolito (MockPasarela / PasarelaPronostix)."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal, InvalidOperation


class ErrorValidacion(Exception):
    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


def _monto(valor) -> Decimal:
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, TypeError) as exc:
        raise ErrorValidacion('"monto" debe ser numerico.', 'monto') from exc
    if monto <= 0:
        raise ErrorValidacion('"monto" debe ser mayor que cero.', 'monto')
    return monto


def validar(datos: dict) -> dict:
    if not isinstance(datos, dict):
        raise ErrorValidacion('El cuerpo debe ser un objeto JSON.')
    if 'orden_id' not in datos:
        raise ErrorValidacion('"orden_id" es obligatorio.', 'orden_id')
    try:
        orden_id = int(datos['orden_id'])
    except (TypeError, ValueError) as exc:
        raise ErrorValidacion('"orden_id" debe ser entero.', 'orden_id') from exc
    if orden_id < 1:
        raise ErrorValidacion('"orden_id" debe ser positivo.', 'orden_id')

    monto = _monto(datos.get('monto'))
    moneda = str(datos.get('moneda') or 'COP')
    modo = str(datos.get('modo') or 'REAL').upper()
    if modo not in {'MOCK', 'REAL'}:
        raise ErrorValidacion('"modo" debe ser MOCK o REAL.', 'modo')
    return {
        'orden_id': orden_id,
        'monto': monto,
        'moneda': moneda,
        'modo': modo,
    }


def evaluar_riesgo(monto: Decimal) -> int:
    return 12 if monto > 0 else 99


def procesar(datos: dict) -> dict:
    payload = validar(datos)
    if payload['modo'] == 'MOCK':
        return {
            'aprobado': True,
            'referencia': 'MOCK-OK',
            'riesgo': 0,
            'modo': 'MOCK',
            'orden_id': payload['orden_id'],
            'monto': str(payload['monto']),
            'moneda': payload['moneda'],
        }

    riesgo = evaluar_riesgo(payload['monto'])
    if riesgo >= 80:
        return {
            'aprobado': False,
            'referencia': None,
            'riesgo': riesgo,
            'modo': 'REAL',
            'motivo': 'Riesgo alto',
            'orden_id': payload['orden_id'],
            'monto': str(payload['monto']),
            'moneda': payload['moneda'],
        }

    referencia = f'PX-{uuid.uuid4().hex[:10].upper()}'
    with open('pasarela_CAMILO_SOTO.log', 'a', encoding='utf-8') as f:
        f.write(
            f'[{datetime.datetime.now()}] Pasarela REAL (ms-pagos) - '
            f'Orden={payload["orden_id"]} Monto=${payload["monto"]} '
            f'Ref={referencia} Riesgo={riesgo} AUTORIZADA+CAPTURADA\n'
        )
    return {
        'aprobado': True,
        'referencia': referencia,
        'riesgo': riesgo,
        'modo': 'REAL',
        'orden_id': payload['orden_id'],
        'monto': str(payload['monto']),
        'moneda': payload['moneda'],
    }
