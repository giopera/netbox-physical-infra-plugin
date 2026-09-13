"""
API URL patterns for Netbox Physical Infra Plugin.

For more information on NetBox REST API routing, see:
https://docs.netbox.dev/en/stable/plugins/development/rest-api/#routers

For Django REST Framework routers, see:
https://www.django-rest-framework.org/api-guide/routers/
"""

from netbox.api.routers import NetBoxRouter

from .views import PhysicalinfraViewSet

app_name = "netbox_physical_infra_plugin"

router = NetBoxRouter()
router.register("physical-infras", PhysicalinfraViewSet)

urlpatterns = router.urls

