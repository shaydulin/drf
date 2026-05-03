from rest_framework import filters
from django.contrib.postgres.search import SearchQuery
from django.db.models.expressions import RawSQL
from rest_framework.exceptions import ValidationError


class GameFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search_query = request.query_params.get("search")
        if not search_query:
            raise ValidationError("Search query parameter is required")

        query = SearchQuery(search_query)
        print(search_query)
        print(query)
        queryset = queryset.filter(
            search_vector=query
        ).annotate(
            rank=RawSQL(
                "ts_rank('{0.1,0.2,0.4,1.0}'::float4[], search_vector, plainto_tsquery(%s), 0)",
                (search_query,)
            )
        ).order_by("-rank")

        return queryset


class UserGameFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        params = request.query_params

        username = params.get("user")
        if not username:
            raise ValidationError("User parameter is required")
        queryset = queryset.filter(user__username=username).order_by("-added_at")

        status = params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset
