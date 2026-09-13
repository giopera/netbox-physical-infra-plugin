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

from .models import Physicalinfra


@strawberry_django.type(
    Physicalinfra,
    fields='__all__',
)
class PhysicalinfraType:
    """GraphQL type for Physicalinfra model."""
    pass


@strawberry.type(name="Query")
class PhysicalinfraQuery:
    """GraphQL queries for Netbox Physical Infra Plugin."""

    physicalinfra: PhysicalinfraType = strawberry_django.field()
    physicalinfra_list: List[PhysicalinfraType] = strawberry_django.field()


schema = [
    PhysicalinfraQuery,
]

