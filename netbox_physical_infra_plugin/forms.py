from django import forms
from django.contrib.contenttypes.models import ContentType

from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from dcim.models import Site, Rack, Cable

from .models import JunctionBox, Conduit, ConnectionPositionChoices


class JunctionBoxForm(NetBoxModelForm):
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=True,
        label='Site'
    )

    fieldsets = (
        ('Junction Box', ('name', 'label', 'site')),
        ('Dimensions & Specifications', (
            'width_mm',
            'height_mm',
            'depth_mm',
            'ip_rating',
            'material',
        )),
        ('Tags', ('tags',)),
    )

    class Meta:
        model = JunctionBox
        fields = (
            'name',
            'label',
            'site',
            'width_mm',
            'height_mm',
            'depth_mm',
            'ip_rating',
            'material',
            'tags',
        )
        labels = {
            'width_mm': 'Width (mm)',
            'height_mm': 'Height (mm)',
            'depth_mm': 'Depth (mm)',
            'ip_rating': 'IP Rating',
        }


class ConduitForm(NetBoxModelForm):
    # Restrict generic foreign key targets to Racks and Junction Boxes
    start_object_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=['rack', 'junctionbox']),
        required=True,
        label='Start Object Type'
    )
    end_object_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=['rack', 'junctionbox']),
        required=True,
        label='End Object Type'
    )

    # Multi-select field for attaching standard NetBox cables inside the conduit
    cables = DynamicModelMultipleChoiceField(
        queryset=Cable.objects.all(),
        required=False,
        label='Routed Cables',
        help_text='Select cables that travel inside this conduit'
    )

    fieldsets = (
        ('Conduit Details', (
            'name',
            'label',
            'length_meters',
            'diameter_mm',
            'max_capacity_percentage',
        )),
        ('Start Termination', (
            'start_object_type',
            'start_object_id',
            'start_position',
        )),
        ('End Termination', (
            'end_object_type',
            'end_object_id',
            'end_position',
        )),
        ('Cable Management', ('cables',)),
        ('Tags', ('tags',)),
    )

    class Meta:
        model = Conduit
        fields = (
            'name',
            'label',
            'length_meters',
            'diameter_mm',
            'max_capacity_percentage',
            'start_object_type',
            'start_object_id',
            'start_position',
            'end_object_type',
            'end_object_id',
            'end_position',
            'cables',
            'tags',
        )
        labels = {
            'length_meters': 'Length (m)',
            'diameter_mm': 'Inner Diameter (mm)',
            'max_capacity_percentage': 'Max Capacity (%)',
        }


# --- Filter Forms (used for searching/filtering lists in the UI) ---

class JunctionBoxFilterForm(NetBoxModelFilterSetForm):
    model = JunctionBox
    
    site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False
    )
    material = forms.CharField(required=False)
    ip_rating = forms.CharField(required=False)


class ConduitFilterForm(NetBoxModelFilterSetForm):
    model = Conduit

    start_position = forms.ChoiceField(
        choices=ConnectionPositionChoices,
        required=False
    )
    end_position = forms.ChoiceField(
        choices=ConnectionPositionChoices,
        required=False
    )