from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet

# Define the connection positions for conduits
class ConnectionPositionChoices(ChoiceSet):
    POSITION_UP = 'up'
    POSITION_DOWN = 'down'
    POSITION_LEFT = 'left'
    POSITION_RIGHT = 'right'
    POSITION_FRONT = 'front'
    POSITION_BACK = 'back'

    CHOICES = (
        (POSITION_UP, 'Up'),
        (POSITION_DOWN, 'Down'),
        (POSITION_LEFT, 'Left'),
        (POSITION_RIGHT, 'Right'),
        (POSITION_FRONT, 'Front'),
        (POSITION_BACK, 'Back'),
    )

class JunctionBox(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100, blank=True, help_text="Physical label on the box")
    
    # Associate with a Site (NetBox standard practice)
    site = models.ForeignKey(to='dcim.Site', on_delete=models.PROTECT, related_name='junction_boxes')
    
    # Measurements
    width_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Width in millimeters")
    height_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Height in millimeters")
    depth_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Depth in millimeters", null=True, blank=True)
    
    # Additional Details
    ip_rating = models.CharField(max_length=20, blank=True, help_text="e.g., IP65, IP67")
    material = models.CharField(max_length=50, blank=True, help_text="e.g., PVC, Steel, Aluminum")

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Junction Boxes'

    def __str__(self):
        return self.name


class Conduit(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100, blank=True)
    
    # Measurements
    length_meters = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    diameter_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Inner diameter in millimeters")
    max_capacity_percentage = models.PositiveSmallIntegerField(default=40, help_text="Max fill percentage (e.g., 40% for NEC code)")

    # Generic Foreign Key for START point (Can be a Rack OR a Junction Box)
    start_object_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='+')
    start_object_id = models.PositiveBigIntegerField()
    start_termination = GenericForeignKey('start_object_type', 'start_object_id')
    start_position = models.CharField(max_length=50, choices=ConnectionPositionChoices, blank=True, help_text="Entry point on the start object")

    # Generic Foreign Key for END point (Can be a Rack OR a Junction Box)
    end_object_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name='+')
    end_object_id = models.PositiveBigIntegerField()
    end_termination = GenericForeignKey('end_object_type', 'end_object_id')
    end_position = models.CharField(max_length=50, choices=ConnectionPositionChoices, blank=True, help_text="Entry point on the end object")

    # Passing Cables through the conduit
    cables = models.ManyToManyField(to='dcim.Cable', related_name='conduits', blank=True, help_text="Cables passing through this conduit")

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    @property
    def current_cable_count(self):
        """Calculates how many cables are inside."""
        return self.cables.count()

    @property
    def occupancy_status(self):
        """
        Calculates occupancy. 
        Note: True fill-ratio requires knowing the diameter of every individual cable. 
        This is a basic count-based example.
        """
        # Example logic: Assume each cable takes roughly 50 sq mm.
        # Area of conduit = pi * (radius)^2
        import math
        radius = float(self.diameter_mm) / 2
        total_area = math.pi * (radius ** 2)
        
        assumed_cable_area = self.current_cable_count * 50.0 # 50 sq mm per cable
        
        if total_area == 0:
            return 0
            
        fill_ratio = (assumed_cable_area / total_area) * 100
        return round(fill_ratio, 2)