from apps.integrations.senet.base import BaseSenetService


class SenetReplenishUserBalanceService(BaseSenetService):
    endpoint = "/api/v2/refill_account/"
    method = "POST"
    save_serializer = None

    def run_request(self):
        return self.fetch(json={
            "devid": self.kwargs["cashdesk_id"],
            "account_id": self.kwargs["account_id"],
            "amount": self.kwargs["amount"],
            "payment_type": 1,  # 1 for card, 2 for cash
            "comment": "Оплата из приложения Lobby"
        })
