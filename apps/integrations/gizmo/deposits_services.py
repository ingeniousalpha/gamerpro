from apps.bookings.models import DepositReplenishment
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import GizmoRequestError


class GizmoCreateDepositTransactionService(BaseGizmoService):
    endpoint = "/api/v2.0/deposittransactions"
    save_serializer = None
    method = "POST"

    def run_service(self):
        return self.fetch(json={
            "userId": self.kwargs.get("user_gizmo_id"),
            "type": 0,
            "amount": int(self.kwargs.get("amount")),
            "paymentMethodId": self.instance.gizmo_payment_method,
            "receiptOverride": True
        })

    def finalize_response(self, response):
        print(response)
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError

        DepositReplenishment.objects.create(
            gizmo_id=response['id'],
            club_branch=self.instance,
            club_user_id=self.kwargs.get('user_gizmo_id'),
            amount=self.kwargs.get('amount')
        )
