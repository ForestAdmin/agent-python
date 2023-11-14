from django.urls import path

from .views import actions, authentication, charts, crud, crud_related, index, stats

app_name = "django_agent"


urlpatterns = [
    # generic
    path("forest/", index.index, name="index"),
    path("forest/scope-cache-invalidation", index.scope_cache_invalidation, name="scope_invalidation"),
    # authentication
    path("forest/authentication", authentication.authentication, name="authentication"),
    path("forest/authentication/callback", authentication.callback, name="authentication_callback"),
    # actions
    path("forest/_actions/<int:action_name>/<slug>/hooks/load", actions.hook, name="action_hook_load"),
    path("forest/_actions/<int:action_name>/<slug>/hooks/change", actions.hook, name="action_hook_change"),
    path("forest/_actions/<int:action_name>/<slug>", actions.execute, name="action_execute"),
    # charts
    path("forest/_charts/<str:chart_name>", charts.chart_datasource, name="datasource_chart"),
    path("forest/_charts/<str:collection_name>/<str:chart_name>", charts.chart_collection, name="collection_chart"),
    # stats
    path("forest/stats/<str:collection_name>", stats.stats, name="stats"),
    # crud related
    path(
        "forest/<str:collection_name>/<str:pks>/relationships/<str:relation_name>/count",
        crud_related.count,
        name="crud_related_count",
    ),
    path(
        "forest/<str:collection_name>/<str:pks>/relationships/<str:relation_name>.csv",
        crud_related.csv,
        name="crud_related_csv",
    ),
    path(
        "forest/<str:collection_name>/<str:pks>/relationships/<str:relation_name>",
        crud_related.list,
        name="crud_related_list",
    ),
    # crud
    path("forest/<str:collection_name>.csv", crud.csv, name="crud_csv"),
    path("forest/<str:collection_name>/count", crud.count, name="crud_count"),
    path("forest/<str:collection_name>/<str:pks>", crud.detail, name="crud_detail"),
    path("forest/<str:collection_name>", crud.list, name="crud_list"),
]
