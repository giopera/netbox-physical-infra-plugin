import django_tables2 as tables
from netbox.tables import NetBoxTable, ChoiceFieldColumn, columns
from .models import JunctionBox, Conduit

class JunctionBoxTable(NetBoxTable):
    # Make the name column a clickable link to the object's detail page
    name = tables.Column(
        linkify=True
    )
    # Make the associated site clickable
    site = tables.Column(
        linkify=True
    )
    # Render tags using NetBox's colored tag UI
    tags = columns.TagColumn(
        url_name='plugins:netbox_cable_pathing:junctionbox_list'
    )

    class Meta(NetBoxTable.Meta):
        model = JunctionBox
        # All available columns a user can turn on via the "Configure Table" button
        fields = (
            'pk', 'id', 'name', 'label', 'site', 'width_mm', 'height_mm',
            'depth_mm', 'ip_rating', 'material', 'tags', 'created', 'last_updated',
        )
        # The columns shown by default when first loading the page
        default_columns = (
            'name', 'site', 'label', 'ip_rating', 'material',
        )


class ConduitTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    # Automatically generate a link to whatever generic object is attached (Rack or Junction Box)
    start_termination = tables.Column(
        linkify=True,
        verbose_name='Start Termination'
    )
    end_termination = tables.Column(
        linkify=True,
        verbose_name='End Termination'
    )
    # Use ChoiceFieldColumn to show human-readable labels (e.g., "Left") instead of DB values ("left")
    start_position = ChoiceFieldColumn()
    end_position = ChoiceFieldColumn()
    
    # Custom properties mapped from models.py
    current_cable_count = tables.Column(
        verbose_name='Cable Count',
        empty_values=()
    )
    occupancy_status = tables.Column(
        verbose_name='Occupancy (%)',
        empty_values=()
    )

    tags = columns.TagColumn(
        url_name='plugins:netbox_cable_pathing:conduit_list'
    )

    class Meta(NetBoxTable.Meta):
        model = Conduit
        fields = (
            'pk', 'id', 'name', 'label', 'length_meters', 'diameter_mm',
            'max_capacity_percentage', 'start_termination', 'start_position',
            'end_termination', 'end_position', 'current_cable_count', 
            'occupancy_status', 'tags', 'created', 'last_updated',
        )
        default_columns = (
            'name', 'start_termination', 'end_termination', 'current_cable_count', 'occupancy_status',
        )