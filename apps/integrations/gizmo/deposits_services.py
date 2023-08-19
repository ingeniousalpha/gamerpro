from apps.bookings.models import DepositReplenishment
from apps.clubs.models import ClubBranchUser
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import GizmoRequestError


class GizmoCreateDepositTransactionService(BaseGizmoService):
    endpoint = "/api/v2.0/deposittransactions"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(json={
            "userId": self.kwargs.get("user_gizmo_id"),
            "amount": int(self.kwargs.get("amount")),
            "type": 0,
            "paymentMethodId": self.instance.gizmo_payment_method,
            "receiptOverride": True
        })

    def finalize_response(self, response):
        print(response)
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError

        return DepositReplenishment.objects.create(
            gizmo_id=response['result']['id'],
            club_branch=self.instance,
            club_user=ClubBranchUser.objects.filter(gizmo_id=self.kwargs.get('user_gizmo_id')).first(),
            amount=self.kwargs.get('amount'),
            commission_amount=self.kwargs.get('commission_amount'),
            total_amount=self.kwargs.get('total_amount'),
            booking=self.kwargs.get('booking'),
            payment_card=self.kwargs.get('payment_card'),
        )
