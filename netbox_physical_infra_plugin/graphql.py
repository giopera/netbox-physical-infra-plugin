"""
GraphQL schema for Netbox Physical Infra Plugin.

For more information on NetBox GraphQL, see:
https://docs.netbox.dev/en/stable/plugins/development/graphql/

For Strawberry GraphQL documentation, see:
https://strawberry.rocks/
"""

from typing import List

import strawberry
import strawberry_django

from .models import Conduit, JunctionBox


@strawberry_django.type(
    JunctionBox,
    fields='__all__',
)
class JunctionBoxType:
    """GraphQL type for JunctionBox model."""
    pass


@strawberry_django.type(Conduit, fields='__all__')
class ConduitType:
    """GraphQL type for Conduit model."""
    pass


@strawberry.type(name="Query")
class PhysicalInfraQuery:
    """GraphQL queries for Netbox Physical Infra Plugin."""

    junctionbox: JunctionBoxType = strawberry_django.field()
    junctionbox_list: List[JunctionBoxType] = strawberry_django.field()
    conduit: ConduitType = strawberry_django.field()
    conduit_list: List[ConduitType] = strawberry_django.field()


schema = [PhysicalInfraQuery]

