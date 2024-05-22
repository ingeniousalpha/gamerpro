from decimal import Decimal

from apps.bookings.models import DepositReplenishment
from apps.clubs.models import ClubBranchUser
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import GizmoRequestError
from constance import config


class GizmoCreateDepositTransactionService(BaseGizmoService):
    endpoint = "/api/v2.0/deposittransactions"
    save_serializer = None
    method = "POST"
    log_response = True

    def run_service(self):
        replenishment_type = self.kwargs.get("replenishment_type") or "deposit"

        self.kwargs["cashback_amount"] = int(self.kwargs.get("user_received_amount") * config.CASHBACK_PERCENT / 100)
        if replenishment_type == "cashback":
            self.kwargs["user_received_amount"] = self.kwargs["cashback_amount"]
        else:
            self.kwargs["user_received_amount"] += self.kwargs["cashback_amount"]

        return self.fetch(json={
            "userId": self.kwargs["user_gizmo_id"],
            "amount": int(self.kwargs["user_received_amount"]),
            "type": 0,
            "paymentMethodId": self.instance.gizmo_payment_method,
            "receiptOverride": True
        })

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError

        return DepositReplenishment.objects.create(
            gizmo_id=response['result']['id'],
            club_branch=self.instance,
            club_user=ClubBranchUser.objects.filter(gizmo_id=self.kwargs.get('user_gizmo_id')).first(),
            user_received_amount=self.kwargs.get('user_received_amount', Decimal(0)),  # amount sent to user balance
            cashback_amount=self.kwargs.get('cashback_amount', Decimal(0)),
            commission_amount=self.kwargs.get('commission_amount'),
            total_amount=self.kwargs.get('total_amount'),
            booking=self.kwargs.get('booking'),
            payment_card=self.kwargs.get('payment_card'),
        )
