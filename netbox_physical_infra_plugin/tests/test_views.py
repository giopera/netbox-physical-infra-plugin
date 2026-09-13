"""
Test cases for Netbox Physical Infra Plugin views.
"""

from django.urls import reverse

from ..models import Physicalinfra
from ..testing import PluginViewTestCase
from ..testing.utils import disable_warnings, get_random_string


class PhysicalinfraViewTestCase(PluginViewTestCase):
    """Test Physicalinfra views."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        Physicalinfra.objects.create(name='View Test 1')
        Physicalinfra.objects.create(name='View Test 2')
        Physicalinfra.objects.create(name='View Test 3')

    def setUp(self):
        """Set up each test."""
        super().setUp()
        self.base_url = 'plugins:netbox_physical_infra_plugin:physicalinfra'

    def test_list_physicalinfras(self):
        """Test Physicalinfra list view."""
        self.add_permissions('netbox_physical_infra_plugin.view_physicalinfra')

        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_list')
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)

    def test_list_physicalinfras_without_permission(self):
        """Test Physicalinfra list view without permission."""
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_list')

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)

    def test_view_physicalinfra(self):
        """Test Physicalinfra detail view."""
        self.add_permissions('netbox_physical_infra_plugin.view_physicalinfra')

        instance = Physicalinfra.objects.first()
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra', kwargs={'pk': instance.pk})
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)
        self.assertEqual(response.context['object'], instance)

    def test_create_physicalinfra(self):
        """Test creating a Physicalinfra via form."""
        self.add_permissions(
            'netbox_physical_infra_plugin.add_physicalinfra',
            'netbox_physical_infra_plugin.view_physicalinfra'
        )

        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_add')
        name = f'Created {get_random_string(10)}'

        form_data = self.post_data({
            'name': name,
        })

        response = self.client.post(url, form_data, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was created
        instance = Physicalinfra.objects.get(name=name)
        self.assertEqual(instance.name, name)

    def test_create_physicalinfra_without_permission(self):
        """Test creating a Physicalinfra without permission."""
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_add')

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)

    def test_edit_physicalinfra(self):
        """Test editing a Physicalinfra via form."""
        self.add_permissions(
            'netbox_physical_infra_plugin.change_physicalinfra',
            'netbox_physical_infra_plugin.view_physicalinfra'
        )

        instance = Physicalinfra.objects.first()
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_edit', kwargs={'pk': instance.pk})

        new_name = f'Edited {get_random_string(10)}'
        form_data = self.post_data({
            'name': new_name,
        })

        response = self.client.post(url, form_data, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was updated
        instance.refresh_from_db()
        self.assertEqual(instance.name, new_name)

    def test_delete_physicalinfra(self):
        """Test deleting a Physicalinfra."""
        self.add_permissions(
            'netbox_physical_infra_plugin.delete_physicalinfra',
            'netbox_physical_infra_plugin.view_physicalinfra'
        )

        instance = Physicalinfra.objects.first()
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_delete', kwargs={'pk': instance.pk})

        # Confirm deletion
        response = self.client.post(url, {'confirm': True}, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was deleted
        self.assertFalse(
            Physicalinfra.objects.filter(pk=instance.pk).exists()
        )

    def test_delete_physicalinfra_without_permission(self):
        """Test deleting a Physicalinfra without permission."""
        instance = Physicalinfra.objects.first()
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_delete', kwargs={'pk': instance.pk})

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)


class PhysicalinfraFormTestCase(PluginViewTestCase):
    """Test Physicalinfra form validation."""

    def setUp(self):
        """Set up each test."""
        super().setUp()
        self.add_permissions(
            'netbox_physical_infra_plugin.add_physicalinfra',
            'netbox_physical_infra_plugin.view_physicalinfra'
        )

    def test_form_validation_empty_name(self):
        """Test form validation with empty name."""
        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_add')
        form_data = self.post_data({'name': ''})

        response = self.client.post(url, form_data)
        self.assertHttpStatus(response, 200)  # Form redisplay

        # Should not create object
        self.assertEqual(Physicalinfra.objects.filter(name='').count(), 0)

    def test_form_validation_duplicate_name(self):
        """Test form validation with duplicate name."""
        Physicalinfra.objects.create(name='Duplicate')

        url = reverse('plugins:netbox_physical_infra_plugin:physicalinfra_add')
        form_data = self.post_data({'name': 'Duplicate'})

        response = self.client.post(url, form_data)
        self.assertHttpStatus(response, 200)  # Form redisplay

        # Should only have one instance with this name
        self.assertEqual(Physicalinfra.objects.filter(name='Duplicate').count(), 1)
