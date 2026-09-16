from netbox.plugins import PluginTemplateExtension

class CableCustomTraceButton(PluginTemplateExtension):
    model = 'dcim.cable'

    def buttons(self):
        cable = self.context['object']
        # Render a button pointing to our custom trace view
        return self.render('netbox_physical_infra_plugin/inc/trace_button.html', {
            'cable': cable,
        })

template_extensions = [CableCustomTraceButton]