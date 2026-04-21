from rest_framework import filters
from django.contrib.postgres.search import SearchQuery
from django.db.models.expressions import RawSQL
from django.db.models.query import QuerySet


class GameSearchFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset: QuerySet, view):
        q = request.query_params.get("search")
        if not q:
            return queryset

        query = SearchQuery(q)
        queryset = queryset.filter(
            search_vector=query
        ).annotate(
            rank=RawSQL(
                "ts_rank('{0.1,0.2,0.4,1.0}'::float4[], search_vector, plainto_tsquery(%s), 0)",
                (q,)
            )
        ).order_by("-rank")

        return queryset
