"""
Netbox Physical Infra Plugin

Plugin configuration for Netbox Physical Infra Plugin.

For a complete list of PluginConfig attributes, see:
https://docs.netbox.dev/en/stable/plugins/development/#pluginconfig-attributes
"""

__author__ = """Giovanni"""
__email__ = "perigio735@gmail.com"
__version__ = "0.1.0"


from netbox.plugins import PluginConfig


class PhysicalinfraConfig(PluginConfig):
    name = "netbox_physical_infra_plugin"
    verbose_name = "Netbox Physical Infra Plugin"
    description = "Netbox plugin for mapping of physical infrastructure like conduits and junction boxes."
    author= "Giovanni"
    author_email = "perigio735@gmail.com"
    version = __version__
    base_url = "netbox_physical_infra_plugin"
    min_version = "4.5.0"
    max_version = "4.5.99"
    graphql_schema = "graphql.schema"


config = PhysicalinfraConfig
