from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ventas.domain.exceptions import ConflictoNegocio, EventoNoEncontrado
from ventas.infra.factories import PasarelaFactory
from ventas.services import CatalogoService, CompraService

from .serializers import ComprarPaseSerializer, EventoSerializer, OrdenCreadaSerializer


class EventoListAPIView(APIView):
    def get(self, request):
        eventos = CatalogoService().listar()
        return Response(EventoSerializer(eventos, many=True).data)


class ComprarPaseAPIView(APIView):
    def post(self, request):
        serializer = ComprarPaseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        servicio = CompraService(pasarela=PasarelaFactory.get_pasarela())
        try:
            resultado = servicio.crear_api(request, serializer.validated_data['evento_id'])
        except EventoNoEncontrado as exc:
            return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ConflictoNegocio as exc:
            return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        payload = OrdenCreadaSerializer(data={
            'orden_id': resultado['orden'].id,
            'total': resultado['orden'].total,
            'estado': resultado['orden'].estado,
            'referencia': resultado['transaccion'].referencia,
        })
        payload.is_valid(raise_exception=True)
        return Response(payload.data, status=status.HTTP_201_CREATED)
