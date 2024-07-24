from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from django.db import models
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.polymorphic_util import DjangoPolymorphismUtil
from forestadmin.datasource_django.utils.type_converter import FilterOperator
from forestadmin.datasource_toolkit.interfaces.fields import (
    is_many_to_one,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    AggregateResult,
    Aggregation,
    Aggregator,
    DateOperation,
    PlainAggregationGroup,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator as ConditionTreeAggregator,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import BaseFilter, Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoQueryBuilder:
    AGGREGATION_FUNC_MAPPING = {
        Aggregator.COUNT: models.Count,
        Aggregator.AVG: models.Avg,
        Aggregator.MAX: models.Max,
        Aggregator.MIN: models.Min,
        Aggregator.SUM: models.Sum,
    }

    @classmethod
    def _normalize_projection(cls, projection: Projection, prefix: str = "") -> Projection:
        # needed to be compliant with the orm result orm
        normalized_projection = [f"{prefix}{col}" for col in projection.columns]
        for parent_field, child_fields in projection.relations.items():
            normalized_projection.extend(cls._normalize_projection(child_fields, f"{prefix}{parent_field}__"))
        return Projection(*normalized_projection)

    @classmethod
    def _mk_base_queryset(
        cls,
        collection: BaseDjangoCollection,
        largest_projection: Projection,
        filter_: BaseFilter,
    ) -> models.QuerySet:
        qs: models.QuerySet = collection.model.objects.all()  # type:ignore

        select_related, prefetch_related = DjangoQueryBuilder._find_related_in_projection(
            collection, largest_projection
        )

        with_generic_fk = DjangoPolymorphismUtil.is_polymorphism_implied(largest_projection, collection)
        if with_generic_fk:
            select_related.union(
                [
                    collection.schema["fields"][generic_fk]["foreign_key_type_field"]  # type:ignore
                    for generic_fk in DjangoPolymorphismUtil.get_polymorphism_relations(largest_projection, collection)
                ]
            )

        qs = qs.select_related(*cls._normalize_projection(Projection(*select_related))).prefetch_related(
            *cls._normalize_projection(Projection(*prefetch_related)),
        )

        condition_tree = filter_.condition_tree
        if condition_tree:
            if any(
                [
                    DjangoPolymorphismUtil.is_type_field_of_generic_fk(field, collection)
                    for field in filter_.condition_tree.projection
                ]
            ):
                condition_tree = DjangoPolymorphismUtil.replace_content_type_in_condition_tree(
                    filter_.condition_tree, collection
                )

        qs = qs.filter(DjangoQueryConditionTreeBuilder.build(condition_tree))

        if isinstance(filter_, PaginatedFilter):
            qs = qs.order_by(*DjangoQueryPaginationBuilder.get_order_by(filter_))
        return qs

    @classmethod
    def _find_related_in_projection(
        cls,
        collection: BaseDjangoCollection,
        projection: Projection,
    ) -> Tuple[Set[str], Set[str]]:
        select_related = set()
        prefetch_related = set()
        break_select_related: Dict[str, bool] = defaultdict(lambda: False)

        for relation_name, subfields in projection.relations.items():
            field_schema = collection.schema["fields"][relation_name]
            if not break_select_related[relation_name]:
                if is_many_to_one(field_schema) or is_one_to_one(field_schema):
                    select_related.add(relation_name)
                elif is_polymorphic_many_to_one(field_schema):
                    select_related.add(field_schema["foreign_key_type_field"])
                    break_select_related[relation_name] = True
                    prefetch_related.add(relation_name)
                elif is_polymorphic_one_to_one(field_schema):
                    break_select_related[relation_name] = True
                    prefetch_related.add(relation_name)

                else:
                    break_select_related[relation_name] = True
                    prefetch_related.add(relation_name)

            sub_select, sub_prefetch = (
                cls._find_related_in_projection(
                    collection.datasource.get_collection(field_schema["foreign_collection"]), subfields
                )
                if subfields != ["*"]
                else ([], [])
            )

            if not break_select_related[relation_name]:
                select_related = select_related.union(Projection(*sub_select).nest(relation_name))
            else:
                prefetch_related = prefetch_related.union(Projection(*sub_select).nest(relation_name))
            prefetch_related = prefetch_related.union(Projection(*sub_prefetch).nest(relation_name))

        return select_related, prefetch_related

    @classmethod
    def mk_list(
        cls,
        collection: BaseDjangoCollection,
        filter_: PaginatedFilter,
        projection: Projection,
    ) -> models.QuerySet:
        full_projection = projection
        if filter_.condition_tree:
            full_projection = full_projection.union(filter_.condition_tree.projection)
        if filter_.sort:
            full_projection = full_projection.union(filter_.sort.projection)
        qs = cls._mk_base_queryset(collection, full_projection, filter_)

        # only raise errors when trying to get a field by a to_many relation
        # or in other words if we have something to pass to prefetch_related
        _, prefetch = cls._find_related_in_projection(collection, full_projection)

        if len(prefetch) == 0 and not DjangoPolymorphismUtil.is_polymorphism_implied(projection, collection):
            qs = qs.only(*cls._normalize_projection(full_projection))
        return DjangoQueryPaginationBuilder.paginate_queryset(qs, filter_)

    @classmethod
    def mk_aggregate(
        cls,
        collection: BaseDjangoCollection,
        filter_: Optional[Filter],
        aggregation: Aggregation,
        limit: Optional[int],
    ) -> List[AggregateResult]:
        full_projection = aggregation.projection
        if filter_.condition_tree:
            full_projection = full_projection.union(filter_.condition_tree.projection)
        qs = cls._mk_base_queryset(collection, full_projection, filter_)

        if aggregation.field:
            qs = qs.order_by(f'-{aggregation.field.replace(":", "__")}')

        if len(aggregation.groups) == 0:
            aggregated_field = aggregation.operation.value
            if aggregation.field is None:
                aggregate_kwargs = {aggregated_field: cls.AGGREGATION_FUNC_MAPPING[aggregation.operation]("*")}
            else:
                aggregate_kwargs = {
                    aggregated_field: cls.AGGREGATION_FUNC_MAPPING[aggregation.operation](aggregation.field)
                }

            qs = qs.aggregate(**aggregate_kwargs)
            value = float(qs[aggregated_field])
            return [{"value": value, "group": {}}]

        else:
            aggregated_field = None
            if aggregation.field is None:
                aggregated_field = aggregation.operation.value
                annotate_kwargs = {aggregated_field: cls.AGGREGATION_FUNC_MAPPING[aggregation.operation]("*")}

            else:
                aggregated_field = aggregation.field.replace(":", "__")
                annotate_kwargs = {
                    aggregated_field: cls.AGGREGATION_FUNC_MAPPING[aggregation.operation](aggregated_field)
                }

            fields = DjangoQueryGroupByHelper.mk_groupby_for_values(aggregation.groups)
            qs = qs.values(*fields)
            qs = qs.annotate(**annotate_kwargs)
            if limit:
                qs = qs[0:limit]

            return [DjangoQueryGroupByHelper.parse_groupby_row(row, aggregation.groups, aggregated_field) for row in qs]

    @staticmethod
    def mk_create(collection: BaseDjangoCollection, data: List[RecordsDataAlias]) -> List[models.Model]:
        instances: List[models.Model] = [
            collection.model.objects.create(**DjangoPolymorphismUtil.replace_content_type_in_patch(d, collection))
            for d in data
        ]
        return instances

    @staticmethod
    def mk_update(
        collection: BaseDjangoCollection,
        filter_: Optional[Filter],
        patch: RecordsDataAlias,
    ):
        patch = DjangoPolymorphismUtil.replace_content_type_in_patch(patch, collection)
        qs = collection.model.objects.filter(
            DjangoQueryConditionTreeBuilder.build(
                DjangoPolymorphismUtil.replace_content_type_in_condition_tree(filter_.condition_tree, collection)
            )
        )
        qs.update(**{k.replace(":", "__"): v for k, v in patch.items()})

    @staticmethod
    def mk_delete(collection: BaseDjangoCollection, filter_: Optional[Filter]):
        qs = collection.model.objects.filter(
            DjangoQueryConditionTreeBuilder.build(
                DjangoPolymorphismUtil.replace_content_type_in_condition_tree(filter_.condition_tree, collection)
            )
        )
        qs.delete()


class DjangoQueryConditionTreeBuilder:
    @classmethod
    def _build_leaf_condition(cls, leaf: ConditionTreeLeaf) -> models.Q:
        field = leaf.field.replace(":", "__")
        key, should_negate = FilterOperator.get_operator(leaf.operator)

        value = leaf.value
        if key == "__isnull":
            value = True
        if should_negate:
            return ~models.Q(**{f"{field}{key}": value})
        else:
            return models.Q(**{f"{field}{key}": value})

    @classmethod
    def _aggregate(cls, aggregator: ConditionTreeAggregator, conditions: List[ConditionTree]) -> models.Q:
        ret: models.Q = models.Q()
        if aggregator == ConditionTreeAggregator.AND:
            for cond in conditions:
                ret &= cond
        elif aggregator == ConditionTreeAggregator.OR:
            for cond in conditions:
                ret |= cond
        else:
            raise DjangoDatasourceException(f"Unable to handle the condition tree aggregator {aggregator}")
        return ret

    @classmethod
    def _build_branch_condition(cls, branch: ConditionTreeBranch) -> models.Q:
        conditions = [DjangoQueryConditionTreeBuilder.build(condition) for condition in branch.conditions]
        return DjangoQueryConditionTreeBuilder._aggregate(branch.aggregator, conditions)

    @classmethod
    def build(cls, condition_tree: Optional[ConditionTree]) -> models.Q:
        if condition_tree is None:
            return models.Q()
        if isinstance(condition_tree, ConditionTreeLeaf):
            return cls._build_leaf_condition(condition_tree)
        elif isinstance(condition_tree, ConditionTreeBranch):
            return cls._build_branch_condition(condition_tree)
        raise DjangoDatasourceException(f"Unable to handle ConditionTree type {condition_tree.__class__}")


class DjangoQueryPaginationBuilder:
    @classmethod
    def get_order_by(cls, filter_: PaginatedFilter) -> List[str]:
        ret = []
        if filter_.sort:
            for sorting in filter_.sort:
                if sorting["ascending"]:
                    ret.append(sorting["field"].replace(":", "__"))
                else:
                    ret.append(f"-{sorting['field'].replace(':', '__')}")
        return ret

    @classmethod
    def paginate_queryset(cls, queryset: models.QuerySet, filter_: PaginatedFilter) -> models.QuerySet:
        if filter_.page:
            return queryset[filter_.page.skip : filter_.page.skip + filter_.page.limit]
        return queryset


class DjangoQueryGroupByHelper:
    DATE_OPERATION_SUFFIX_MAPPING: Dict[DateOperation, str] = {
        DateOperation.DAY: "__day",
        DateOperation.WEEK: "__week",
        DateOperation.MONTH: "__month",
        DateOperation.YEAR: "__year",
    }

    @classmethod
    def get_operation_suffixes(cls, group: PlainAggregationGroup) -> List[str]:
        if not group.get("operation"):
            return None

        if group["operation"] == DateOperation.YEAR:
            return [cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.YEAR]]
        if group["operation"] == DateOperation.MONTH:
            return [
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.YEAR],
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.MONTH],
            ]
        if group["operation"] == DateOperation.WEEK:
            return [
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.YEAR],
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.WEEK],
            ]
        if group["operation"] == DateOperation.DAY:
            return [
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.YEAR],
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.MONTH],
                cls.DATE_OPERATION_SUFFIX_MAPPING[DateOperation.DAY],
            ]

    @classmethod
    def mk_groupby_for_values(cls, groups: List[PlainAggregationGroup]) -> List[str]:
        values = []
        for group in groups:
            value = group["field"].replace(":", "__")

            suffixes = cls.get_operation_suffixes(group)
            if suffixes:
                values.extend([f"{value}{suffix}" for suffix in suffixes])

            else:
                values.append(value)
        return values

    @classmethod
    def parse_groupby_row(
        cls, row: Dict[str, Any], groups: List[PlainAggregationGroup], aggregated_field: str
    ) -> AggregateResult:
        groupby = {}
        for group in groups:
            suffixes = cls.get_operation_suffixes(group)
            field_name = group["field"].replace(":", "__")
            if not suffixes:
                groupby[group["field"]] = row[field_name]
            else:
                groupby[group["field"]] = cls._make_date_from_record(row, field_name, group["operation"])

        return {"value": float(row[aggregated_field]), "group": groupby}

    @classmethod
    def _make_date_from_record(cls, row: AggregateResult, date_field: str, date_operation: DateOperation) -> date:
        if date_operation == DateOperation.YEAR:
            return date(row[f"{date_field}__year"], 1, 1)

        if date_operation == DateOperation.MONTH:
            return date(row[f"{date_field}__year"], row[f"{date_field}__month"], 1)

        if date_operation == DateOperation.WEEK:
            str_year_week = f'{row[f"{date_field}__year"]}-W{row[f"{date_field}__week"]}'
            row_date = datetime.strptime(str_year_week + "-1", "%Y-W%W-%w")
            return row_date.date()

        if date_operation == DateOperation.DAY:
            return date(row[f"{date_field}__year"], row[f"{date_field}__month"], row[f"{date_field}__day"])
