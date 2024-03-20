from apps.clubs.models import ClubTimePacketGroup
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
                    gizmo_id=time_packet_group['id'],
                    club_branch_id=self.instance.id
                ).exists():
                    try:
                        serializer = self.save_serializer(data={
                            "gizmo_id": time_packet_group['id'],
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
        return self.fetch(path_params={"limit": ParamKeyWords["limit"].get(self.instance.api_host, "Limit")})

    def save(self, response):
        resp = response.get('result')
        if resp and len(resp.get('data', [])) > 0:
            resp_data = resp.get('data')
            for time_packet in resp_data:
                try:
                    packet_group = self.instance.packet_groups.filter(
                        gizmo_id=time_packet['productGroupId']
                    ).first()
                    if packet_group:
                        serializer = self.save_serializer(data={
                            "gizmo_id": time_packet['id'],
                            "gizmo_name": time_packet['name'],
                            "display_name": time_packet['name'],
                            "description": time_packet.get('description'),
                            "price": time_packet['price'],
                            "minutes": time_packet.get('timeProduct', {}).get('minutes', 0),
                            "packet_group": packet_group.id,
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
        return self.fetch(path_params={
            "user_id": self.kwargs.get('user_id'),
            "time": int(self.kwargs.get('minutes')),
            "price": int(self.kwargs.get('price')),
            "payment_method": self.instance.gizmo_payment_method
        })

    def finalize_response(self, response):
        if response.get('isError') == True:
            self.log_error(str(response['errors']))
            raise GizmoRequestError
