from django.urls import path
from netbox.views.generic import ObjectChangeLogView
from . import models, views

urlpatterns = (
    # -------------------------------------------------------------------------
    # Junction Box URLs
    # -------------------------------------------------------------------------
    path('junction-boxes/', views.JunctionBoxListView.as_view(), name='junctionbox_list'),
    path('junction-boxes/add/', views.JunctionBoxEditView.as_view(), name='junctionbox_add'),
    path('junction-boxes/<int:pk>/', views.JunctionBoxView.as_view(), name='junctionbox'),
    path('junction-boxes/<int:pk>/edit/', views.JunctionBoxEditView.as_view(), name='junctionbox_edit'),
    path('junction-boxes/<int:pk>/delete/', views.JunctionBoxDeleteView.as_view(), name='junctionbox_delete'),
    
    # Built-in NetBox changelog view
    path('junction-boxes/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='junctionbox_changelog', kwargs={
        'model': models.JunctionBox
    }),
    
    # Bulk operations
    path('junction-boxes/delete/', views.JunctionBoxBulkDeleteView.as_view(), name='junctionbox_bulk_delete'),


    # -------------------------------------------------------------------------
    # Conduit URLs
    # -------------------------------------------------------------------------
    path('conduits/', views.ConduitListView.as_view(), name='conduit_list'),
    path('conduits/add/', views.ConduitEditView.as_view(), name='conduit_add'),
    path('conduits/<int:pk>/', views.ConduitView.as_view(), name='conduit'),
    path('conduits/<int:pk>/edit/', views.ConduitEditView.as_view(), name='conduit_edit'),
    path('conduits/<int:pk>/delete/', views.ConduitDeleteView.as_view(), name='conduit_delete'),
    
    # Built-in NetBox changelog view
    path('conduits/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='conduit_changelog', kwargs={
        'model': models.Conduit
    }),
    
    # Bulk operations
    path('conduits/delete/', views.ConduitBulkDeleteView.as_view(), name='conduit_bulk_delete'),
)