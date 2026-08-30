from rest_framework import serializers

from ventas.models import Evento


class EventoSerializer(serializers.ModelSerializer):
    local = serializers.StringRelatedField()
    visitante = serializers.StringRelatedField()
    competicion = serializers.StringRelatedField()

    class Meta:
        model = Evento
        fields = (
            'id',
            'local',
            'visitante',
            'competicion',
            'fecha',
            'fase',
            'precio_pase',
            'estado',
        )


class ComprarPaseSerializer(serializers.Serializer):
    evento_id = serializers.IntegerField(min_value=1)


class OrdenCreadaSerializer(serializers.Serializer):
    orden_id = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado = serializers.CharField()
    referencia = serializers.CharField()
