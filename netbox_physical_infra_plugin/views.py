from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from django.contrib import messages

from dcim.models import Cable
from netbox.views import generic
from . import forms, models, tables, filtersets
from .svg_generator import generate_conduit_trace_svg

# -------------------------------------------------------------------------
# Junction Box Views
# -------------------------------------------------------------------------

class JunctionBoxView(generic.ObjectView):
    queryset = models.JunctionBox.objects.all()

    def get_extra_context(self, request, instance):
        # Embeds the child terminal table on the parent page
        terminals_table = tables.TerminalTable(instance.terminals.all())
        terminals_table.configure(request)
        return {
            'terminals_table': terminals_table
        }

class JunctionBoxListView(generic.ObjectListView):
    queryset = models.JunctionBox.objects.all()
    table = tables.JunctionBoxTable
    filterset = filtersets.JunctionBoxFilterSet
    filterset_form = forms.JunctionBoxFilterForm

class JunctionBoxEditView(generic.ObjectEditView):
    queryset = models.JunctionBox.objects.all()
    form = forms.JunctionBoxForm

class JunctionBoxDeleteView(generic.ObjectDeleteView):
    queryset = models.JunctionBox.objects.all()

class JunctionBoxBulkDeleteView(generic.BulkDeleteView):
    queryset = models.JunctionBox.objects.all()
    filterset = filtersets.JunctionBoxFilterSet
    table = tables.JunctionBoxTable

# -------------------------------------------------------------------------
# Terminal Views
# -------------------------------------------------------------------------

class TerminalView(generic.ObjectView):
    queryset = models.Terminal.objects.all()

class TerminalListView(generic.ObjectListView):
    queryset = models.Terminal.objects.all()
    table = tables.TerminalTable
    filterset = filtersets.TerminalFilterSet
    filterset_form = forms.TerminalFilterForm

class TerminalEditView(generic.ObjectEditView):
    queryset = models.Terminal.objects.all()
    form = forms.TerminalForm

class TerminalDeleteView(generic.ObjectDeleteView):
    queryset = models.Terminal.objects.all()

class TerminalBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Terminal.objects.all()
    filterset = filtersets.TerminalFilterSet
    table = tables.TerminalTable

class TerminalBulkAddView(View):
    """Custom view for adding multiple terminals to a Box at once using pattern expansion."""
    def get(self, request, *args, **kwargs):
        initial = {'junction_box': request.GET.get('junction_box')}
        form = forms.TerminalBulkAddForm(initial=initial)
        return render(request, 'generic/object_edit.html', {
            'form': form,
            'object': models.Terminal(),
            'return_url': self.get_return_url(request)
        })

    def post(self, request, *args, **kwargs):
        form = forms.TerminalBulkAddForm(request.POST)
        if form.is_valid():
            names = form.cleaned_data['name_pattern']
            box = form.cleaned_data['junction_box']
            pos = form.cleaned_data['position']
            desc = form.cleaned_data['description']
            
            for name in names:
                models.Terminal.objects.create(junction_box=box, name=name, position=pos, description=desc)
                
            messages.success(request, f"Added {len(names)} terminals to {box}.")
            return redirect(box.get_absolute_url())
            
        return render(request, 'generic/object_edit.html', {
            'form': form,
            'object': models.Terminal(),
            'return_url': self.get_return_url(request)
        })

    def get_return_url(self, request):
        if 'junction_box' in request.GET:
            box = models.JunctionBox.objects.filter(pk=request.GET['junction_box']).first()
            if box: return box.get_absolute_url()
        return ''

# -------------------------------------------------------------------------
# Conduit Views
# -------------------------------------------------------------------------

class ConduitView(generic.ObjectView):
    queryset = models.Conduit.objects.all()

    def get_extra_context(self, request, instance):
        return {
            'routed_cables': instance.cables.all(),
            'current_cable_count': instance.current_cable_count,
            'occupancy_status': instance.occupancy_status,
        }

class ConduitListView(generic.ObjectListView):
    queryset = models.Conduit.objects.all()
    table = tables.ConduitTable
    filterset = filtersets.ConduitFilterSet
    filterset_form = forms.ConduitFilterForm

class ConduitEditView(generic.ObjectEditView):
    queryset = models.Conduit.objects.all()
    form = forms.ConduitForm

class ConduitDeleteView(generic.ObjectDeleteView):
    queryset = models.Conduit.objects.all()

class ConduitBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Conduit.objects.all()
    filterset = filtersets.ConduitFilterSet
    table = tables.ConduitTable

class CableConduitCustomTraceView(generic.ObjectView):
    queryset = Cable.objects.all()
    template_name = 'netbox_physical_infra_plugin/pathtrace.html'

    def get(self, request, pk):
        cable = get_object_or_404(Cable, pk=pk)
        print(cable)
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