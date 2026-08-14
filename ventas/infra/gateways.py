import datetime
import uuid

from ..domain.interfaces import PasarelaPago


class MockPasarela(PasarelaPago):
    """Implementacion MOCK: imprime en consola, sin cobro real."""

    def procesar(self, transaccion) -> bool:
        print(
            f'[DEBUG] Mock Pasarela: autoriza y captura ${transaccion.monto} '
            f'sin cargo real (orden {transaccion.orden_id}).'
        )
        transaccion.aprobar(referencia='MOCK-OK')
        return True


class PasarelaPronostix(PasarelaPago):
    """
    Implementacion REAL de la pasarela propia: evalua riesgo,
    autoriza y captura, dejando rastro de auditoria.
    """

    def evaluar_riesgo(self, transaccion) -> int:
        return 12 if transaccion.monto > 0 else 99

    def procesar(self, transaccion) -> bool:
        score = self.evaluar_riesgo(transaccion)
        if score >= 80:
            transaccion.rechazar(motivo='Riesgo alto')
            return False

        referencia = f'PX-{uuid.uuid4().hex[:10].upper()}'
        archivo_log = 'pasarela_CAMILO_SOTO.log'
        with open(archivo_log, 'a', encoding='utf-8') as f:
            f.write(
                f'[{datetime.datetime.now()}] Pasarela REAL - '
                f'Orden={transaccion.orden_id} Monto=${transaccion.monto} '
                f'Ref={referencia} Riesgo={score} AUTORIZADA+CAPTURADA\n'
            )
        transaccion.aprobar(referencia=referencia)
        return True
