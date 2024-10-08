from apps.integrations.senet.base import BaseSenetService
from apps.integrations.senet.serializers import SenetTimePacketCreateSerializer


class SenetGetTimePacketsService(BaseSenetService):
    endpoint = "/api/v2/ticket/?office_id={office_id}"
    save_serializer = SenetTimePacketCreateSerializer
    method = "GET"

    def run_request(self):
        return self.fetch(path_params={"office_id": self.instance.outer_id})

    def save(self, response):
        for time_packet in response:
            try:
                computer_group = self.instance.computer_groups.filter(
                    outer_id=time_packet['zones'][0]
                ).first()
                if computer_group:
                    serializer = self.save_serializer(
                        data={
                            "outer_id": time_packet['id'],
                            "outer_name": time_packet['name'],
                            "display_name": time_packet['name'],
                            "price": time_packet['price'],
                            "minutes": time_packet['duration_period_length']*60,
                            "club_computer_group": computer_group.id,
                        }
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
            except Exception as e:
                self.log_error(e)
