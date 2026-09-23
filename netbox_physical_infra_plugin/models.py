import math
from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet

class ConnectionPositionChoices(ChoiceSet):
    POSITION_UP = 'up'
    POSITION_DOWN = 'down'
    POSITION_LEFT = 'left'
    POSITION_RIGHT = 'right'

    CHOICES = (
        (POSITION_UP, 'Up'),
        (POSITION_DOWN, 'Down'),
        (POSITION_LEFT, 'Left'),
        (POSITION_RIGHT, 'Right'),
    )

class JunctionBox(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100, blank=True, help_text="Physical label on the box")
    
    site = models.ForeignKey(to='dcim.Site', on_delete=models.PROTECT, related_name='junction_boxes')
    
    width_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Width in millimeters")
    height_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Height in millimeters")
    depth_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Depth in millimeters", null=True, blank=True)
    
    ip_rating = models.CharField(max_length=20, blank=True, help_text="e.g., IP65, IP67")
    material = models.CharField(max_length=50, blank=True, help_text="e.g., PVC, Steel, Aluminum")

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Junction Boxes'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Fallback dynamic reverse to ensure views redirect correctly
        return reverse('plugins:netbox_physical_infra_plugin:junctionbox', args=[self.pk])

    @property
    def terminal_visualizer(self):
        """Groups physical terminal objects by position for the template UI."""
        terminals = self.terminals.all()
        return {
            'up': terminals.filter(position=ConnectionPositionChoices.POSITION_UP),
            'down': terminals.filter(position=ConnectionPositionChoices.POSITION_DOWN),
            'left': terminals.filter(position=ConnectionPositionChoices.POSITION_LEFT),
            'right': terminals.filter(position=ConnectionPositionChoices.POSITION_RIGHT),
        }


class Terminal(NetBoxModel):
    """Represents a single discrete connection point on a Junction Box."""
    junction_box = models.ForeignKey(to=JunctionBox, on_delete=models.CASCADE, related_name='terminals')
    name = models.CharField(max_length=100, help_text="e.g., Port 1, T1")
    position = models.CharField(max_length=50, choices=ConnectionPositionChoices)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ('junction_box', 'name')
        unique_together = ('junction_box', 'name')

    def __str__(self):
        return f"{self.junction_box.name} - {self.name}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_physical_infra_plugin:terminal', args=[self.pk])

    @property
    def is_connected(self):
        """Checks if any conduit is terminated to this specific terminal."""
        return self.connected_conduits.exists()

    @property
    def connected_conduits(self):
        """Returns all conduits connected to this terminal as start or end termination."""
        ctype = ContentType.objects.get_for_model(self)
        return Conduit.objects.filter(
            models.Q(start_object_type=ctype, start_object_id=self.pk) |
            models.Q(end_object_type=ctype, end_object_id=self.pk)
        )


class Conduit(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100, blank=True)
    
    length_meters = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    diameter_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Inner diameter in millimeters")
    max_capacity_percentage = models.PositiveSmallIntegerField(default=40, help_text="Max fill percentage")

    start_object_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='+')
    start_object_id = models.PositiveBigIntegerField()
    start_termination = GenericForeignKey('start_object_type', 'start_object_id')
    
    end_object_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='+')
    end_object_id = models.PositiveBigIntegerField()
    end_termination = GenericForeignKey('end_object_type', 'end_object_id')
    
    cables = models.ManyToManyField(to='dcim.Cable', related_name='conduits', blank=True, help_text="Cables passing through")

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    @property
    def current_cable_count(self):
        return self.cables.count()

    @property
    def occupancy_status(self):
        radius = float(self.diameter_mm) / 2
        total_area = math.pi * (radius ** 2)
        assumed_cable_area = self.current_cable_count * 50.0 
        
        if total_area == 0:
            return 0
            
        fill_ratio = (assumed_cable_area / total_area) * 100
        return round(fill_ratio, 2)