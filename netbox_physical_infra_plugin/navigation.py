from netbox.plugins import PluginMenuItem, PluginMenuButton
from utilities.choices import ButtonColorChoices

# Define the Add button for Junction Boxes
junctionbox_buttons = [
    PluginMenuButton(
        link='plugins:netbox_cable_pathing:junctionbox_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

# Define the Add button for Conduits
conduit_buttons = [
    PluginMenuButton(
        link='plugins:netbox_cable_pathing:conduit_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

# Register the menu items
menu_items = (
    PluginMenuItem(
        link='plugins:netbox_cable_pathing:junctionbox_list',
        link_text='Junction Boxes',
        permissions=['netbox_cable_pathing.view_junctionbox'],
        buttons=junctionbox_buttons
    ),
    PluginMenuItem(
        link='plugins:netbox_cable_pathing:conduit_list',
        link_text='Conduits',
        permissions=['netbox_cable_pathing.view_conduit'],
        buttons=conduit_buttons
    ),
)