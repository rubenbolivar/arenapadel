from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    reservation_details = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'user', 'reservation', 'reservation_details', 'amount', 
                 'payment_method', 'status', 'proof_of_payment', 'created_at', 
                 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']

    def get_reservation_details(self, obj):
        if obj.reservation:
            return {
                'court': obj.reservation.court.name,
                'start_time': obj.reservation.start_time,
                'end_time': obj.reservation.end_time,
            }
        return None

    def validate(self, data):
        if data.get('payment_method') == 'transfer' and not data.get('proof_of_payment'):
            raise serializers.ValidationError({
                'proof_of_payment': 'Proof of payment is required for bank transfers'
            })
        return data
