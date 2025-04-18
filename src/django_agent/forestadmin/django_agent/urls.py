from django.conf import settings
from django.urls import path, re_path

from .views import actions, authentication, capabilities, charts, crud, crud_related, index, native_query, stats

app_name = "django_agent"


prefix = getattr(settings, "FOREST_PREFIX", "")
if len(prefix) > 0 and prefix[-1] != "/":
    prefix = f"{prefix}/"
if len(prefix) > 0 and prefix[0] == "/":
    prefix = f"{prefix[1:]}"

urlpatterns = [
    # generic
    path(f"{prefix}forest/", index.index, name="index"),
    path(f"{prefix}forest/_internal/capabilities", capabilities.capabilities, name="capabilities"),
    path(f"{prefix}forest/_internal/native_query", native_query.native_query, name="capabilities"),
    path(f"{prefix}forest/scope-cache-invalidation", index.scope_cache_invalidation, name="scope_invalidation"),
    # authentication
    path(f"{prefix}forest/authentication", authentication.authentication, name="authentication"),
    path(f"{prefix}forest/authentication/callback", authentication.callback, name="authentication_callback"),
    # actions
    path(
        f"{prefix}forest/_actions/<str:collection_name>/<int:action_name>/<slug>/hooks/load",
        actions.hook,
        name="action_hook_load",
    ),
    path(
        f"{prefix}forest/_actions/<str:collection_name>/<int:action_name>/<slug>/hooks/change",
        actions.hook,
        name="action_hook_change",
    ),
    path(
        f"{prefix}forest/_actions/<str:collection_name>/<int:action_name>/<slug>/hooks/search",
        actions.hook,
        name="action_hook_search",
    ),
    path(
        f"{prefix}forest/_actions/<str:collection_name>/<int:action_name>/<slug>",
        actions.execute,
        name="action_execute",
    ),
    # charts
    path(f"{prefix}forest/_charts/<str:chart_name>", charts.chart_datasource, name="datasource_chart"),
    path(
        f"{prefix}forest/_charts/<str:collection_name>/<str:chart_name>",
        charts.chart_collection,
        name="collection_chart",
    ),
    # stats
    path(f"{prefix}forest/stats/<str:collection_name>", stats.stats, name="stats"),
    # crud related
    re_path(
        f"{prefix}forest/(?P<collection_name>[^/]+)/(?P<pks>.*)/relationships/(?P<relation_name>[^/]+)/count",
        crud_related.count,
        name="crud_related_count",
    ),
    re_path(
        f"{prefix}forest/(?P<collection_name>[^/]+)/(?P<pks>.*)/relationships/(?P<relation_name>[^/]+).csv",
        crud_related.csv,
        name="crud_related_csv",
    ),
    re_path(
        f"{prefix}forest/(?P<collection_name>[^/]+)/(?P<pks>.*)/relationships/(?P<relation_name>[^/]+)",
        crud_related.list_,
        name="crud_related_list",
    ),
    # crud
    path(f"{prefix}forest/<str:collection_name>.csv", crud.csv, name="crud_csv"),
    path(f"{prefix}forest/<str:collection_name>/count", crud.count, name="crud_count"),
    re_path(f"{prefix}forest/(?P<collection_name>[^/]+)/(?P<pks>.+)", crud.detail, name="crud_detail"),
    path(f"{prefix}forest/<str:collection_name>", crud.list_, name="crud_list"),
]
