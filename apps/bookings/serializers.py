from django.db import transaction
from rest_framework import serializers

from apps.authentication.exceptions import UserNotFound
from apps.bookings.models import Booking, BookedComputer
from apps.bookings.services import gizmo_book_computers
from apps.clubs.exceptions import ComputerDoesNotBelongToClubBranch, ComputerIsAlreadyBooked
from apps.clubs.models import ClubComputer
from apps.common.serializers import RequestUserPropertyMixin


class CreateBookingUsingBalanceSerializer(RequestUserPropertyMixin, serializers.ModelSerializer):
    computers = serializers.ListField(write_only=True)

    class Meta:
        model = Booking
        fields = (
            'club_branch',
            'computers',
        )

    def validate(self, attrs):
        print(attrs)
        return attrs

    def create(self, validated_data):
        club_user = self.user.get_club_accont(validated_data['club_branch'])
        if not club_user:
            raise UserNotFound
        validated_data['club_user'] = club_user

        computers = []
        for computer_id in validated_data.pop('computers'):
            computer = validated_data['club_branch'].computers.filter(id=computer_id).first()
            if not computer:
                raise ComputerDoesNotBelongToClubBranch
            if computer.is_booked:
                raise ComputerIsAlreadyBooked
            computers.append(computer)

        with transaction.atomic():
            print(validated_data)
            booking = super().create(validated_data)
            print("booking created: ", booking)
            # for computer in computers:
            #     BookedComputer.objects.create(booking=booking, computer=computer)
            # gizmo_book_computers(**validated_data, computers=computers)

        return booking
