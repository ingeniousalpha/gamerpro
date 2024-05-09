from rest_framework.response import Response
from rest_framework import pagination, status


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'count'

    def get_paginated_response(self, data):
        data = {
            'count': len(data),
            'total_count':  self.page.paginator.count,
            'page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data,
        }
        return Response(data, status=status.HTTP_200_OK)


class ClubsPagination(CustomPagination):
    page_size = 20
