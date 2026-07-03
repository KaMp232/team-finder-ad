import json

from django.core.paginator import Paginator
from django.http import JsonResponse

from .constants import JSON_CONTENT_TYPE

PAGE_QUERY_PARAM = "page"
FIRST_PAGE_NUMBER = 1


def json_error(message, status):
    return JsonResponse({"error": message}, status=status)


def paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get(PAGE_QUERY_PARAM, FIRST_PAGE_NUMBER))
    params = request.GET.copy()
    params.pop(PAGE_QUERY_PARAM, None)
    query_prefix = params.urlencode()
    if query_prefix:
        query_prefix += "&"
    return page_obj, query_prefix


def request_payload(request):
    if request.content_type == JSON_CONTENT_TYPE:
        try:
            return json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST
