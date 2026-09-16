from netbox.plugins import PluginMenuItem, PluginMenuButton
from netbox.choices import ButtonColorChoices

# Define the Add button for Junction Boxes
junctionbox_buttons = [
    PluginMenuButton(
        link='plugins:netbox_physical_infra_plugin:junctionbox_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

# Define the Add button for Conduits
conduit_buttons = [
    PluginMenuButton(
        link='plugins:netbox_physical_infra_plugin:conduit_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

# Register the menu items
menu_items = (
    PluginMenuItem(
        link='plugins:netbox_physical_infra_plugin:junctionbox_list',
        link_text='Junction Boxes',
        permissions=['netbox_physical_infra_plugin.view_junctionbox'],
        buttons=junctionbox_buttons
    ),
    PluginMenuItem(
        link='plugins:netbox_physical_infra_plugin:conduit_list',
        link_text='Conduits',
        permissions=['netbox_physical_infra_plugin.view_conduit'],
        buttons=conduit_buttons
    ),
)