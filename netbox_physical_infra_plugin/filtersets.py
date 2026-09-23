import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from dcim.models import Site, Cable

from .models import JunctionBox, Terminal, Conduit

class JunctionBoxFilterSet(NetBoxModelFilterSet):
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
    q = django_filters.CharFilter(method='search', label='Search')

    class Meta:
        model = JunctionBox
        fields = ('id', 'name', 'label', 'width_mm', 'height_mm', 'depth_mm', 'ip_rating', 'material')

    def search(self, queryset, name, value):
        if not value.strip(): return queryset
        return queryset.filter(Q(name__icontains=value) | Q(label__icontains=value))


class TerminalFilterSet(NetBoxModelFilterSet):
    junction_box_id = django_filters.ModelMultipleChoiceFilter(
        queryset=JunctionBox.objects.all(),
        label='Junction Box (ID)'
    )
    q = django_filters.CharFilter(method='search', label='Search')

    class Meta:
        model = Terminal
        fields = ('id', 'name', 'position')

    def search(self, queryset, name, value):
        if not value.strip(): return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class ConduitFilterSet(NetBoxModelFilterSet):
    cable_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cables',
        queryset=Cable.objects.all(),
        label='Cables',
    )
    q = django_filters.CharFilter(method='search', label='Search')

    class Meta:
        model = Conduit
        fields = ('id', 'name', 'label', 'length_meters', 'diameter_mm', 'max_capacity_percentage')

    def search(self, queryset, name, value):
        if not value.strip(): return queryset
        return queryset.filter(Q(name__icontains=value) | Q(label__icontains=value))