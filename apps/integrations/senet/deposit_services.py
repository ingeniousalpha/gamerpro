import logging

from apps.integrations.senet.base import BaseSenetCashboxService
from apps.integrations.senet.exceptions import SenetInvalidCashboxCredentials, SenetNoActiveCashbox

logger = logging.getLogger("senet")


class SenetGetCashboxIDService(BaseSenetCashboxService):
    endpoint = "/api/v2/cashdesk_office/?paginate=false"
    method = "GET"
    save_serializer = None

    def run_request(self):
        return self.fetch()

    def finalize_response(self, response):
        if not isinstance(response, list):
            logger.error(str(response))
            raise SenetInvalidCashboxCredentials
        cashbox_id = None
        for office in response:
            if int(self.instance.outer_id) == office["office_id"]:
                for cashbox in office["cashdesks"]:
                    if (
                        cashbox["is_online"]
                        and cashbox["has_employee_session"]
                        and cashbox["has_cashdesk_session"]
                    ):
                        cashbox_id = cashbox["devid"]
                        break
            if cashbox_id:
                break
        if not cashbox_id:
            raise SenetNoActiveCashbox
        return cashbox_id


class SenetReplenishUserBalanceService(BaseSenetCashboxService):
    endpoint = "/api/v2/refill_account/"
    method = "POST"
    save_serializer = None

    def run_request(self):
        cashbox_id = SenetGetCashboxIDService(instance=self.instance).run()
        return self.fetch(json={
            "devid": cashbox_id,
            "account_id": self.kwargs["account_id"],
            "amount": self.kwargs["amount"],
            "payment_type": 1,
            "comment": "Оплата из приложения Lobby"
        })
