from typing import Dict

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.exceptions import ConflictError, ForbiddenError, RequireApproval
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, Aggregator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SmartActionChecker:
    def __init__(
        self,
        request: "ActionRequest",  # noqa: F821
        collection: Collection,
        smart_action: Dict,
        caller: User,
        role_id: int,
        filter_: Filter,
    ):
        self.request = request
        self.collection = collection
        self.smart_action = smart_action
        self.caller = caller
        self.role_id = role_id
        self.filter_ = filter_

    async def can_execute(self) -> bool:
        if self.request.body.get("data", {}).get("attributes", {}).get("signed_approval_request") is None:
            return await self._can_trigger()
        else:
            return await self._can_approve()

    async def _can_approve(self) -> bool:
        if (
            self.role_id in self.smart_action["userApprovalEnabled"]
            and (
                len(self.smart_action["userApprovalConditions"]) == 0
                or await self._match_conditions("userApprovalConditions")
            )
            and (
                self.request.body.get("data", {}).get("attributes", {}).get("requester_id") != self.caller.user_id
                or self.role_id in self.smart_action["selfApprovalEnabled"]
            )
        ):
            return True

        raise ForbiddenError(
            "You don't have the permission to trigger this action", {}, "CustomActionTriggerForbiddenError"
        )

    async def _can_trigger(self) -> bool:
        if (
            self.role_id in self.smart_action["triggerEnabled"]
            and self.role_id not in self.smart_action["approvalRequired"]
        ):
            if len(self.smart_action["triggerConditions"]) == 0 or await self._match_conditions("triggerConditions"):
                return True
        elif (
            self.role_id in self.smart_action["triggerEnabled"]
            and self.role_id in self.smart_action["approvalRequired"]
        ):
            if len(self.smart_action["approvalRequiredConditions"]) == 0 or await self._match_conditions(
                "approvalRequiredConditions"
            ):
                raise RequireApproval(
                    "This action requires to be approved.",
                    {},
                    "CustomActionRequiresApprovalError",
                    self.smart_action["userApprovalEnabled"],
                )
            else:
                if len(self.smart_action["triggerConditions"]) == 0 or await self._match_conditions(
                    "triggerConditions"
                ):
                    return True

        raise ForbiddenError(
            "You don't have the permission to trigger this action.", {}, "CustomActionTriggerForbiddenError"
        )

    async def _match_conditions(self, condition_name: str) -> bool:
        try:
            pk_field = SchemaUtils.get_primary_keys(self.collection.schema)[0]
            if self.request.body.get("data", {}).get("attributes", {}).get("all_records"):
                condition_record_filter = ConditionTreeLeaf(
                    pk_field,
                    Operator.NOT_EQUAL,
                    self.request.body.get("data", {}).get("attributes", {}).get("all_records_ids_excluded"),
                )
            else:
                condition_record_filter = ConditionTreeLeaf(
                    pk_field,
                    Operator.IN,
                    self.request.body.get("data", {}).get("attributes", {}).get("ids"),
                )
            condition = self.smart_action[condition_name][0]["filter"]
            conditional_filter = self.filter_.override(
                {
                    "condition_tree": ConditionTreeFactory.intersect(
                        [
                            ConditionTreeFactory.from_plain_object(condition),
                            self.filter_.condition_tree,
                            condition_record_filter,
                        ]
                    )
                }
            )

            rows = await self.collection.aggregate(
                self.caller, conditional_filter, Aggregation({"operation": Aggregator.COUNT})
            )
            return (rows[0]["value"] or 0) == len(self.request.body.get("data", {}).get("attributes", {}).get("ids"))
        except Exception:
            raise ConflictError(
                "The conditions to trigger this action cannot be verified. Please contact an administrator.",
                {},
                "InvalidActionConditionError",
            )
