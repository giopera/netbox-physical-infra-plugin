"""
API serializers for Netbox Physical Infra Plugin.

Serializers are required for NetBox event handling (webhooks, change logging).
They also power the REST API endpoints.

For more information on NetBox REST API serializers, see:
https://docs.netbox.dev/en/stable/plugins/development/rest-api/#serializers

For Django REST Framework serializers, see:
https://www.django-rest-framework.org/api-guide/serializers/
"""

from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from ..models import Conduit, JunctionBox


class JunctionBoxSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_physical_infra_plugin-api:junctionbox-detail"
    )

    class Meta:
        model = JunctionBox
        fields = (
            "id", "url", "display", "name", "label", "site", "width_mm",
            "height_mm", "depth_mm", "ip_rating", "material", "tags",
            "custom_fields", "created", "last_updated",
        )


class ConduitSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_physical_infra_plugin-api:conduit-detail"
    )

    class Meta:
        model = Conduit
        fields = (
            "id", "url", "display", "name", "label", "length_meters",
            "diameter_mm", "max_capacity_percentage", "start_object_type",
            "start_object_id", "start_position", "end_object_type",
            "end_object_id", "end_position", "cables", "tags", "custom_fields",
            "created", "last_updated",
        )
