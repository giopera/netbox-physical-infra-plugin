from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet
from dcim.models import Cable, Rack, Site

from .models import JunctionBox, Conduit, ConnectionPositionChoices


class JunctionBoxForm(NetBoxModelForm):
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=True,
        label='Site'
    )

    fieldsets = (
        FieldSet('name', 'label', 'site', name='Junction Box'),
        FieldSet(
            'width_mm',
            'height_mm',
            'depth_mm',
            'ip_rating',
            'material',
            name='Dimensions & Specifications',
        ),
        FieldSet('tags', name='Tags'),
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
    start_termination = forms.ChoiceField(required=True, label='Start Termination')
    end_termination = forms.ChoiceField(required=True, label='End Termination')

    # Multi-select field for attaching standard NetBox cables inside the conduit
    cables = DynamicModelMultipleChoiceField(
        queryset=Cable.objects.all(),
        required=False,
        label='Routed Cables',
        help_text='Select cables that travel inside this conduit'
    )

    fieldsets = (
        FieldSet(
            'name',
            'label',
            'length_meters',
            'diameter_mm',
            'max_capacity_percentage',
            name='Conduit Details',
        ),
        FieldSet(
            'start_termination', 'start_position',
            name='Start Termination',
        ),
        FieldSet(
            'end_termination', 'end_position',
            name='End Termination',
        ),
        FieldSet('cables', name='Cable Management'),
        FieldSet('tags', name='Tags'),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The generic foreign-key storage fields are required in Meta.fields so
        # Django can build the model form, but the combined selectors replace
        # them in the UI.
        for field_name in (
            'start_object_type',
            'start_object_id',
            'end_object_type',
            'end_object_id',
        ):
            self.fields.pop(field_name, None)

        choices = [('', '---------')]
        choices.extend(
            (self._termination_value(obj), f'Rack: {obj}')
            for obj in Rack.objects.all().order_by('name')
        )
        choices.extend(
            (self._termination_value(obj), f'Junction Box: {obj}')
            for obj in JunctionBox.objects.all().order_by('name')
        )
        self.fields['start_termination'].choices = choices
        self.fields['end_termination'].choices = choices

        if self.instance.pk:
            self.initial['start_termination'] = self._termination_value(self.instance.start_termination)
            self.initial['end_termination'] = self._termination_value(self.instance.end_termination)

    @staticmethod
    def _termination_value(obj):
        if obj is None:
            return ''
        return f'{obj._meta.app_label}:{obj._meta.model_name}:{obj.pk}'

    @staticmethod
    def _termination_object(value):
        app_label, model_name, object_id = value.split(':', 2)
        if (app_label, model_name) == ('dcim', 'rack'):
            return Rack.objects.get(pk=object_id)
        if (app_label, model_name) == ('netbox_physical_infra_plugin', 'junctionbox'):
            return JunctionBox.objects.get(pk=object_id)
        raise forms.ValidationError('Select a Rack or Junction Box.')

    def clean(self):
        cleaned_data = super().clean() or self.cleaned_data
        for prefix in ('start', 'end'):
            field_name = f'{prefix}_termination'
            value = cleaned_data.get(field_name)
            if not value:
                continue
            try:
                setattr(self.instance, f'{prefix}_termination', self._termination_object(value))
            except (JunctionBox.DoesNotExist, Rack.DoesNotExist, ValueError):
                self.add_error(field_name, 'Select a valid Rack or Junction Box.')
        return cleaned_data


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