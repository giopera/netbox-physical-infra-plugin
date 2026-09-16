from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from dcim.models import Cable
from netbox.views import generic
from . import forms, models, tables, filtersets
from .svg_generator import generate_conduit_trace_svg
from .tracer import trace_cable_path

# -------------------------------------------------------------------------
# Junction Box Views
# -------------------------------------------------------------------------

class JunctionBoxView(generic.ObjectView):
    """Detail view for a single Junction Box"""
    queryset = models.JunctionBox.objects.all()


class JunctionBoxListView(generic.ObjectListView):
    """List view for all Junction Boxes (creates the data table page)"""
    queryset = models.JunctionBox.objects.all()
    table = tables.JunctionBoxTable
    filterset = filtersets.JunctionBoxFilterSet
    filterset_form = forms.JunctionBoxFilterForm


class JunctionBoxEditView(generic.ObjectEditView):
    """View for creating or editing a Junction Box"""
    queryset = models.JunctionBox.objects.all()
    form = forms.JunctionBoxForm


class JunctionBoxDeleteView(generic.ObjectDeleteView):
    """View for deleting a single Junction Box"""
    queryset = models.JunctionBox.objects.all()


class JunctionBoxBulkDeleteView(generic.BulkDeleteView):
    """View for deleting multiple Junction Boxes from the list view"""
    queryset = models.JunctionBox.objects.all()
    filterset = filtersets.JunctionBoxFilterSet
    table = tables.JunctionBoxTable


# -------------------------------------------------------------------------
# Conduit Views
# -------------------------------------------------------------------------

class ConduitView(generic.ObjectView):
    """Detail view for a single Conduit"""
    queryset = models.Conduit.objects.all()

    def get_extra_context(self, request, instance):
        """
        Pass custom calculated values to the HTML template so you can display
        the measurements and occupancy values on the conduit's page.
        """
        return {
            'routed_cables': instance.cables.all(),
            'current_cable_count': instance.current_cable_count,
            'occupancy_status': instance.occupancy_status,
        }


class ConduitListView(generic.ObjectListView):
    """List view for all Conduits"""
    queryset = models.Conduit.objects.all()
    table = tables.ConduitTable
    filterset = filtersets.ConduitFilterSet
    filterset_form = forms.ConduitFilterForm


class ConduitEditView(generic.ObjectEditView):
    """View for creating or editing a Conduit"""
    queryset = models.Conduit.objects.all()
    form = forms.ConduitForm


class ConduitDeleteView(generic.ObjectDeleteView):
    """View for deleting a single Conduit"""
    queryset = models.Conduit.objects.all()


class ConduitBulkDeleteView(generic.BulkDeleteView):
    """View for deleting multiple Conduits from the list view"""
    queryset = models.Conduit.objects.all()
    filterset = filtersets.ConduitFilterSet
    table = tables.ConduitTable


class CableConduitCustomTraceView(generic.ObjectView):
    queryset = Cable.objects.all()
    template_name = 'netbox_physical_infra_plugin/pathtrace.html'

    def get(self, request, pk):
        cable = get_object_or_404(Cable, pk=pk)
        svg_content = generate_conduit_trace_svg(cable)

        return render(request, self.template_name, {
            'object': cable,
            'svg_content': svg_content,
        })


class CableConduitSVGDownloadView(generic.ObjectView):
    queryset = Cable.objects.all()

    def get(self, request, pk):
        cable = get_object_or_404(Cable, pk=pk)
        svg_content = generate_conduit_trace_svg(cable)
        filename = f'cable-{cable.pk}-path-trace.svg'

        response = HttpResponse(svg_content, content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response