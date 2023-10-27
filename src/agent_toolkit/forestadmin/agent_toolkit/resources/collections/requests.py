from typing import Any, Dict, Optional, TypedDict, TypeVar, Union

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.datasource_toolkit.collections import Collection, CollectionException
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import (
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from typing_extensions import Self

BoundCollection = TypeVar("BoundCollection", bound=Collection)


class RequestCollectionException(AgentToolkitException):
    pass


class RequestArgs(TypedDict):
    method: RequestMethod
    collection: Union[Collection, CollectionCustomizer]
    body: Optional[Dict[str, Any]]
    query: Optional[Dict[str, str]]
    headers: Optional[Dict[str, str]]
    user: Optional[User]


class RequestCollection(Request):
    def __init__(
        self,
        method: RequestMethod,
        collection: Union[Collection, CollectionCustomizer],
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        user: Optional[User] = None,
    ):
        super(RequestCollection, self).__init__(method, body, query, headers, user)
        self.collection = collection

    @staticmethod
    def from_request_args(
        request: Request, datasource: Union[Datasource[BoundCollection], DatasourceCustomizer]
    ) -> RequestArgs:
        if not request.query:
            raise RequestCollectionException("'collection_name' is missing in the request")
        try:
            collection_name = request.query["collection_name"]
        except KeyError:
            raise RequestCollectionException("'collection_name' is missing in the request")
        try:
            collection = datasource.get_collection(collection_name)
        except DatasourceException:
            raise RequestCollectionException(f"Collection '{collection_name}' not found")

        return RequestArgs(
            method=request.method,
            body=request.body,
            query=request.query,
            headers=request.headers,
            user=request.user,
            collection=collection,
        )

    @classmethod
    def from_request(
        cls, request: Request, datasource: Union[Datasource[BoundCollection], DatasourceCustomizer]
    ) -> Self:
        return cls(**cls.from_request_args(request, datasource))

    @property
    def pks(self):
        if not self.query:
            raise CollectionResourceException("")
        try:
            pks = self.query["pks"]
        except KeyError:
            raise CollectionResourceException("primary keys are missing")
        return pks


class RequestRelationCollection(RequestCollection):
    def __init__(
        self,
        method: RequestMethod,
        collection: Union[Collection, CollectionCustomizer],
        foreign_collection: Union[Collection, CollectionCustomizer],
        relation: Union[ManyToMany, OneToMany, OneToOne, ManyToOne],
        relation_name: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        user: Optional[User] = None,
    ):
        super(RequestRelationCollection, self).__init__(method, collection, body, query, headers, user)
        self.foreign_collection = foreign_collection
        self.relation = relation
        self.relation_name = relation_name

    @classmethod
    def from_request(
        cls, request: Request, datasource: Union[Datasource[BoundCollection], DatasourceCustomizer]
    ) -> Self:
        kwargs = cls.from_request_args(request, datasource)
        if not request.query:
            raise RequestCollectionException("'relation_name' is missing in the request")
        try:
            relation_name = request.query["relation_name"]
        except KeyError:
            raise RequestCollectionException("'relation_name' is missing in the request")

        try:
            related_field = kwargs["collection"].get_field(relation_name)
        except CollectionException:
            raise RequestCollectionException(
                f"{relation_name} is an unknown relation for the collection {kwargs['collection'].name}"
            )

        if (
            is_many_to_one(related_field)
            or is_one_to_one(related_field)
            or is_many_to_many(related_field)
            or is_one_to_many(related_field)
        ):
            try:
                foreign_collection = datasource.get_collection(related_field["foreign_collection"])
            except DatasourceException:
                raise RequestCollectionException(f"Collection '{relation_name}' not found")
            return cls(
                relation=related_field, relation_name=relation_name, foreign_collection=foreign_collection, **kwargs
            )
        else:
            raise RequestCollectionException(f"'{relation_name}' is not a related field")
