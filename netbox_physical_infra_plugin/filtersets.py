import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from dcim.models import Site, Cable

from .models import JunctionBox, Conduit

class JunctionBoxFilterSet(NetBoxModelFilterSet):
    # Allow filtering by one or more Sites
    site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        label='Site (ID)',
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name='site__slug',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label='Site (Slug)',
    )
    
    # Global search (the main search bar at the top of the list view)
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = JunctionBox
        fields = (
            'id', 'name', 'label', 'width_mm', 'height_mm', 
            'depth_mm', 'ip_rating', 'material',
        )

    def search(self, queryset, name, value):
        """
        Defines how the global search bar behaves.
        Here, it searches for matches in the name or label fields.
        """
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(label__icontains=value)
        )


class ConduitFilterSet(NetBoxModelFilterSet):
    # Allow filtering by one or more attached cables
    cable_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cables',
        queryset=Cable.objects.all(),
        label='Cables',
    )
    
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = Conduit
        fields = (
            'id', 'name', 'label', 'length_meters', 'diameter_mm', 
            'max_capacity_percentage', 'start_position', 'end_position',
        )

    def search(self, queryset, name, value):
        """
        Defines how the global search bar behaves for conduits.
        """
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(label__icontains=value)
        )