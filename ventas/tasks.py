import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='ventas.notificar_compra_pase')
def notificar_compra_pase(orden_id, evento_id, usuario, total, referencia):
    """
    Tarea de fondo tras una compra exitosa.
    En produccion enviaria correo; aqui deja rastro en el log del worker.
    """
    mensaje = (
        f'Notificacion de compra: orden={orden_id} evento={evento_id} '
        f'usuario={usuario} total={total} ref={referencia}'
    )
    logger.info(mensaje)
    return mensaje
