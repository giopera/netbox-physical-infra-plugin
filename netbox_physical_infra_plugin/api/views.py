"""
API viewsets for Netbox Physical Infra Plugin.

For more information on NetBox REST API viewsets, see:
https://docs.netbox.dev/en/stable/plugins/development/rest-api/#viewsets

For Django REST Framework viewsets, see:
https://www.django-rest-framework.org/api-guide/viewsets/
"""

from netbox.api.viewsets import NetBoxModelViewSet

from ..models import Conduit, JunctionBox
from .serializers import ConduitSerializer, JunctionBoxSerializer


class JunctionBoxViewSet(NetBoxModelViewSet):
    queryset = JunctionBox.objects.all()
    serializer_class = JunctionBoxSerializer


class ConduitViewSet(NetBoxModelViewSet):
    queryset = Conduit.objects.all()
    serializer_class = ConduitSerializer

