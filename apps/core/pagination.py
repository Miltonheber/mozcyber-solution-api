from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """?page=1&size=20 (size máx. 100)."""

    page_size = 20
    page_query_param = "page"
    page_size_query_param = "size"
    max_page_size = 100
