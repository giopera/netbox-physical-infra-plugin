import django_tables2 as tables
from netbox.tables import NetBoxTable, ChoiceFieldColumn, columns
from .models import JunctionBox, Terminal, Conduit

class JunctionBoxTable(NetBoxTable):
    name = tables.Column(linkify=True)
    site = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name='plugins:netbox_physical_infra_plugin:junctionbox_list')

    class Meta(NetBoxTable.Meta):
        model = JunctionBox
        fields = ('pk', 'id', 'name', 'label', 'site', 'width_mm', 'height_mm', 'depth_mm', 'ip_rating', 'material', 'tags', 'created', 'last_updated')
        default_columns = ('name', 'site', 'label', 'ip_rating', 'material')


class TerminalTable(NetBoxTable):
    name = tables.Column(linkify=True)
    junction_box = tables.Column(linkify=True)
    position = ChoiceFieldColumn()
    is_connected = columns.BooleanColumn(accessor='is_connected', verbose_name='Connected')
    tags = columns.TagColumn(url_name='plugins:netbox_physical_infra_plugin:terminal_list')

    class Meta(NetBoxTable.Meta):
        model = Terminal
        fields = ('pk', 'id', 'name', 'junction_box', 'position', 'is_connected', 'description', 'actions')
        default_columns = ('name', 'position', 'is_connected', 'description', 'actions')


class ConduitTable(NetBoxTable):
    name = tables.Column(linkify=True)
    start_termination = tables.Column(linkify=True, verbose_name='Start Termination')
    end_termination = tables.Column(linkify=True, verbose_name='End Termination')

    
    current_cable_count = tables.Column(verbose_name='Cable Count', empty_values=())
    occupancy_status = tables.Column(verbose_name='Occupancy (%)', empty_values=())
    tags = columns.TagColumn(url_name='plugins:netbox_physical_infra_plugin:conduit_list')

    class Meta(NetBoxTable.Meta):
        model = Conduit
        fields = ('pk', 'id', 'name', 'label', 'length_meters', 'diameter_mm', 'max_capacity_percentage', 'start_termination', 'end_termination', 'current_cable_count', 'occupancy_status', 'tags', 'created', 'last_updated')
        default_columns = ('name', 'start_termination', 'end_termination', 'current_cable_count', 'occupancy_status')