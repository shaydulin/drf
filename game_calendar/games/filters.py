from rest_framework import filters
from django.contrib.postgres.search import SearchQuery
from django.db.models.expressions import RawSQL
from rest_framework.exceptions import ValidationError


class GameFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        params = request.query_params

        keys = set(params.keys())
        if not keys:
            raise ValidationError("At least one filter parameter is required")

        allowed = [
            {'search'},
            {'user'},
            {'user', 'status'},
        ]

        if not any(keys <= a for a in allowed):
            raise ValidationError("Invalid filter combination")

        search_query = params.get('search')
        user = params.get('user')
        status = params.get('status')

        if search_query:
            query = SearchQuery(search_query)
            queryset = queryset.filter(
                search_vector=query
            ).annotate(
                rank=RawSQL(
                    "ts_rank('{0.1,0.2,0.4,1.0}'::float4[], search_vector, plainto_tsquery(%s), 0)",
                    (search_query,)
                )
            ).order_by("-rank")

        if user:
            queryset = queryset.filter(user_links__user__username=user)

        if status:
            queryset = queryset.filter(user_links__status=status)

        return queryset


# class GameSearchFilter(filters.BaseFilterBackend):
#     def filter_queryset(self, request, queryset: QuerySet, view):
#         q = request.query_params.get("search")
#         if not q:
#             return queryset

#         query = SearchQuery(q)
#         queryset = queryset.filter(
#             search_vector=query
#         ).annotate(
#             rank=RawSQL(
#                 "ts_rank('{0.1,0.2,0.4,1.0}'::float4[], search_vector, plainto_tsquery(%s), 0)",
#                 (q,)
#             )
#         ).order_by("-rank")

#         return queryset


# class UserGameFilterSet(FilterSet):
#     user = CharFilter(field_name='user__username')
    
#     class Meta:
#         model = UserGame
#         fields = ['status', 'user']

#     def get_form_class(self):
#         form_class = super().get_form_class()

#         class CustomForm(form_class):
#             def clean(self):
#                 cleaned_data = super().clean()
#                 user_value = self.data.get('user')
#                 if user_value:
#                     User = get_user_model()
#                     if not User.objects.filter(username=user_value).exists():
#                         self.add_error('user', f'User "{user_value}" does not exist.')
#                 else:
#                     self.add_error('user', 'This field is required.')
#                 return cleaned_data

#         return CustomForm
