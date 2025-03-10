import time

from apps.clubs.models import ClubTimePacketGroup
from apps.integrations.exceptions import ServiceNotFound, ServiceUnavailable
from apps.integrations.gizmo import ParamKeyWords
from apps.integrations.gizmo.base import BaseGizmoService
from apps.integrations.gizmo.exceptions import GizmoRequestError
from apps.integrations.gizmo.serializers import GizmoTimePacketGroupSaveSerializer, GizmoTimePacketSaveSerializer


class GizmoGetTimePacketGroupsService(BaseGizmoService):
    endpoint = "/api/v2.0/productgroups?{limit}=100"
    save_serializer = GizmoTimePacketGroupSaveSerializer
    method = "GET"

    def run_service(self):
        return self.fetch(path_params={"limit": ParamKeyWords["limit"].get(self.instance.api_host, "Limit")})

    def save(self, response):
        resp = response.get('result')
        if resp and len(resp.get('data', [])) > 0:
            resp_data = resp.get('data')
            for time_packet_group in resp_data:
                if not ClubTimePacketGroup.objects.filter(
                    outer_id=time_packet_group['id'],
                    club_branch_id=self.instance.id
                ).exists():
                    try:
                        serializer = self.save_serializer(data={
                            "outer_id": time_packet_group['id'],
                            "name": time_packet_group['name'],
                            "club_branch": self.instance.id,
                        })
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    except Exception as e:
                        self.log_error(e)


class GizmoGetTimePacketsService(BaseGizmoService):
    endpoint = "/api/v2.0/products?ProductType=1&IsDeleted=false&{limit}=150"
    save_serializer = GizmoTimePacketSaveSerializer
    method = "GET"

    def run_service(self):
        return self.fetch(path_params={"limit": ParamKeyWords["limit"].get(self.instance.api_host, "Pagination.Limit")})

    def save(self, response):
        resp = response.get('result')
        if resp and len(resp.get('data', [])) > 0:
            resp_data = resp.get('data')
            for time_packet in resp_data:
                try:
                    packet_group = self.instance.packet_groups.filter(
                        outer_id=time_packet['productGroupId']
                    ).first()
                    computer_group = packet_group.computer_group

                    if packet_group:
                        serializer = self.save_serializer(data={
                            "outer_id": time_packet['id'],
                            "outer_name": time_packet['name'],
                            "display_name": time_packet['name'],
                            "description": time_packet.get('description'),
                            "price": time_packet['price'],
                            "minutes": time_packet.get('timeProduct', {}).get('minutes', 0),
                            "packet_group": packet_group.id,
                            "club_computer_group": computer_group.id,
                        })
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                except Exception as e:
                    self.log_error(e)


class GizmoAddPaidTimeToUser(BaseGizmoService):
    endpoint = "/api/users/{user_id}/order/time/{time}/price/{price}/invoice/payment/{payment_method}"
    save_serializer = None
    method = "POST"
    log_response = True

    def run_service(self):
        error = None
        for i in range(0, 5):
            try:
                response = self.fetch(path_params={
                    "user_id": self.kwargs.get('user_id'),
                    "time": int(self.kwargs.get('minutes')),
                    "price": int(self.kwargs.get('price')),
                    "payment_method": self.instance.gizmo_payment_method
                })
                error = None
                break
            except (ServiceNotFound, ServiceUnavailable) as e:
                error = e

        if error:
            raise error
        return response

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError


class GizmoSetTimePacketToUser(BaseGizmoService):
    endpoint = "/api/users/{user_id}/order/{product_id}/{quantity}/invoice/payment/{payment_method}"
    save_serializer = None
    method = "POST"
    log_response = True

    def run_service(self):
        error = None
        for i in range(0, 5):
            try:
                print(f"Request Attempt {self.__class__.__name__}: {i+1}")
                response = self.fetch(path_params={
                    "user_id": self.kwargs.get('user_id'),
                    "product_id": int(self.kwargs.get('product_id')),  # Gizmo Time Packet ID
                    "quantity": int(self.kwargs.get('quantity', 1)),
                    "payment_method": self.instance.gizmo_points_method if self.kwargs.get('by_points') else self.instance.gizmo_payment_method
                })
                error = None
                break
            except (ServiceNotFound, ServiceUnavailable) as e:
                error = e
                time.sleep(1)

        if error:
            raise error
        return response

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError
        elif response.get('result') == 16384:
            error_msg = "Вы не можете сесть за этот компьютер"
            self.log_error(error_msg)
            raise GizmoRequestError(error_msg)


class GizmoSetPointsToUser(BaseGizmoService):
    endpoint = "/api/points/{user_id}/{amount}"
    save_serializer = None
    method = "POST"
    log_response = False

    def run_service(self):
        error = None
        for i in range(0, 5):
            try:
                response = self.fetch(path_params={
                    "user_id": self.kwargs.get('user_id'),
                    "amount": int(self.kwargs.get('amount')),
                })
                error = None
                break
            except (ServiceNotFound, ServiceUnavailable) as e:
                error = e

        if error:
            raise error
        return response

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response))
            raise GizmoRequestError
