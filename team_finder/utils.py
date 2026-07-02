from django.core.paginator import Paginator

PAGE_QUERY_PARAM = "page"


def paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get(PAGE_QUERY_PARAM))
    params = request.GET.copy()
    params.pop(PAGE_QUERY_PARAM, None)
    query_prefix = params.urlencode()
    if query_prefix:
        query_prefix += "&"
    return page_obj, query_prefix
