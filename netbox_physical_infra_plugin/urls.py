from django.urls import path
from netbox.views.generic import ObjectChangeLogView
from . import models, views

app_name = 'netbox_physical_infra_plugin'

urlpatterns = (
    # -------------------------------------------------------------------------
    # Junction Box URLs
    # -------------------------------------------------------------------------
    path('junction-boxes/', views.JunctionBoxListView.as_view(), name='junctionbox_list'),
    path('junction-boxes/add/', views.JunctionBoxEditView.as_view(), name='junctionbox_add'),
    path('junction-boxes/<int:pk>/', views.JunctionBoxView.as_view(), name='junctionbox'),
    path('junction-boxes/<int:pk>/edit/', views.JunctionBoxEditView.as_view(), name='junctionbox_edit'),
    path('junction-boxes/<int:pk>/delete/', views.JunctionBoxDeleteView.as_view(), name='junctionbox_delete'),
    path('junction-boxes/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='junctionbox_changelog', kwargs={'model': models.JunctionBox}),
    path('junction-boxes/delete/', views.JunctionBoxBulkDeleteView.as_view(), name='junctionbox_bulk_delete'),

    # -------------------------------------------------------------------------
    # Terminal URLs
    # -------------------------------------------------------------------------
    path('terminals/', views.TerminalListView.as_view(), name='terminal_list'),
    path('terminals/add/', views.TerminalEditView.as_view(), name='terminal_add'),
    path('terminals/bulk-add/', views.TerminalBulkAddView.as_view(), name='terminal_bulk_add'),
    path('terminals/<int:pk>/', views.TerminalView.as_view(), name='terminal'),
    path('terminals/<int:pk>/edit/', views.TerminalEditView.as_view(), name='terminal_edit'),
    path('terminals/<int:pk>/delete/', views.TerminalDeleteView.as_view(), name='terminal_delete'),
    path('terminals/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='terminal_changelog', kwargs={'model': models.Terminal}),
    path('terminals/delete/', views.TerminalBulkDeleteView.as_view(), name='terminal_bulk_delete'),

    # -------------------------------------------------------------------------
    # Conduit URLs
    # -------------------------------------------------------------------------
    path('conduits/', views.ConduitListView.as_view(), name='conduit_list'),
    path('conduits/add/', views.ConduitEditView.as_view(), name='conduit_add'),
    path('conduits/<int:pk>/', views.ConduitView.as_view(), name='conduit'),
    path('conduits/<int:pk>/edit/', views.ConduitEditView.as_view(), name='conduit_edit'),
    path('conduits/<int:pk>/delete/', views.ConduitDeleteView.as_view(), name='conduit_delete'),
    path('conduits/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='conduit_changelog', kwargs={'model': models.Conduit}),
    path('conduits/delete/', views.ConduitBulkDeleteView.as_view(), name='conduit_bulk_delete'),
    path('cables/<int:pk>/path-trace/', views.CableConduitCustomTraceView.as_view(), name='cable_custom_trace'),
    path('cables/<int:pk>/path-trace/download/', views.CableConduitSVGDownloadView.as_view(), name='cable_trace_download'),
)