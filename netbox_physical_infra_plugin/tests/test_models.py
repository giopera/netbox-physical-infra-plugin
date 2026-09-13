"""
Test cases for Netbox Physical Infra Plugin models.
"""

from django.core.exceptions import ValidationError

from ..models import Physicalinfra
from ..testing import PluginModelTestCase
from ..testing.utils import create_tags, get_random_string


class PhysicalinfraTestCase(PluginModelTestCase):
    """Test Physicalinfra model."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create test instances
        Physicalinfra.objects.create(name='Test 1')
        Physicalinfra.objects.create(name='Test 2')
        Physicalinfra.objects.create(name='Test 3')

    def test_create_physicalinfra(self):
        """Test creating a Physicalinfra instance."""
        name = f'Test {get_random_string(10)}'
        instance = Physicalinfra.objects.create(name=name)

        self.assertEqual(instance.name, name)
        self.assertIsNotNone(instance.pk)

    def test_physicalinfra_str(self):
        """Test Physicalinfra string representation."""
        instance = Physicalinfra.objects.first()
        self.assertEqual(str(instance), instance.name)

    def test_physicalinfra_absolute_url(self):
        """Test Physicalinfra get_absolute_url method."""
        instance = Physicalinfra.objects.first()
        url = instance.get_absolute_url()

        self.assertIsNotNone(url)
        self.assertIn(str(instance.pk), url)

    def test_physicalinfra_unique_name(self):
        """Test that Physicalinfra names must be unique."""
        name = 'Duplicate Name'
        Physicalinfra.objects.create(name=name)

        with self.assertRaises(ValidationError):
            instance = Physicalinfra(name=name)
            instance.full_clean()

    def test_model_to_dict(self):
        """Test model_to_dict helper method."""
        instance = Physicalinfra.objects.first()
        data = self.model_to_dict(instance)

        self.assertIn('name', data)
        self.assertEqual(data['name'], instance.name)
        self.assertIn('id', data)

    def test_instance_equal(self):
        """Test assertInstanceEqual helper method."""
        instance = Physicalinfra.objects.first()

        # Should pass with matching data
        self.assertInstanceEqual(
            instance,
            {'name': instance.name, 'id': instance.pk}
        )

    def test_physicalinfra_with_tags(self):
        """Test Physicalinfra with tags."""
        tags = create_tags(['important', 'test'])
        instance = Physicalinfra.objects.first()

        instance.tags.add(*tags)
        instance.save()

        self.assertEqual(instance.tags.count(), 2)
        self.assertIn(tags[0], instance.tags.all())

    def test_bulk_create(self):
        """Test bulk creation of Physicalinfra instances."""
        initial_count = Physicalinfra.objects.count()

        instances = [
            Physicalinfra(name=f'Bulk {i}')
            for i in range(5)
        ]
        Physicalinfra.objects.bulk_create(instances)

        self.assertEqual(
            Physicalinfra.objects.count(),
            initial_count + 5
        )

    def test_query_filter(self):
        """Test filtering Physicalinfra instances."""
        # Create a specific instance for filtering
        test_name = f'FilterTest {get_random_string(10)}'
        Physicalinfra.objects.create(name=test_name)

        # Test filter
        results = Physicalinfra.objects.filter(name=test_name)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, test_name)

    def test_ordering(self):
        """Test Physicalinfra default ordering."""
        instances = list(Physicalinfra.objects.all())

        # Check that instances are ordered by name
        names = [instance.name for instance in instances]
        self.assertEqual(names, sorted(names))


class PhysicalinfraValidationTestCase(PluginModelTestCase):
    """Test Physicalinfra validation."""

    def test_empty_name(self):
        """Test that empty name is not allowed."""
        with self.assertRaises(ValidationError):
            instance = Physicalinfra(name='')
            instance.full_clean()

    def test_name_max_length(self):
        """Test name field max length."""
        long_name = 'x' * 101  # Exceeds max_length of 100

        with self.assertRaises(ValidationError):
            instance = Physicalinfra(name=long_name)
            instance.full_clean()
