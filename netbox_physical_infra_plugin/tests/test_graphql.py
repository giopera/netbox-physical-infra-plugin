"""
Test cases for Netbox Physical Infra Plugin GraphQL API.
"""
from ..models import Physicalinfra
from ..testing import PluginGraphQLTestCase


class PhysicalinfraGraphQLTestCase(PluginGraphQLTestCase):
    """Test Physicalinfra GraphQL queries."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        Physicalinfra.objects.create(name='GraphQL Test 1')
        Physicalinfra.objects.create(name='GraphQL Test 2')
        Physicalinfra.objects.create(name='GraphQL Test 3')

    def test_query_physicalinfra(self):
        """Test GraphQL query for a single Physicalinfra."""
        self.add_permissions('netbox_physical_infra_plugin.view_physicalinfra')

        instance = Physicalinfra.objects.first()

        query = (
            "query { "
            "physicalinfra(id: " + str(instance.pk) + ") { "
            "id name "
            "} "
            "}"
        )

        response = self.execute_query(query)
        self.assertIsNone(response.get('errors'))

        data = response['data']['physicalinfra']
        self.assertEqual(data['id'], str(instance.pk))
        self.assertEqual(data['name'], instance.name)

    def test_query_physicalinfra_list(self):
        """Test GraphQL query for list of Physicalinfras."""
        self.add_permissions('netbox_physical_infra_plugin.view_physicalinfra')

        query = """
        query {
            physicalinfra_list {
                id
                name
            }
        }
        """

        response = self.execute_query(query)
        self.assertIsNone(response.get('errors'))

        data = response['data']['physicalinfra_list']
        self.assertEqual(len(data), 3)
        self.assertIn('id', data[0])
        self.assertIn('name', data[0])

    def test_query_physicalinfra_with_all_fields(self):
        """Test GraphQL query with all available fields."""
        self.add_permissions('netbox_physical_infra_plugin.view_physicalinfra')

        instance = Physicalinfra.objects.first()

        query = (
            "query { "
            "physicalinfra(id: " + str(instance.pk) + ") { "
            "id name created last_updated "
            "} "
            "}"
        )

        response = self.execute_query(query)
        self.assertIsNone(response.get('errors'))

        data = response['data']['physicalinfra']
        self.assertEqual(data['id'], str(instance.pk))
        self.assertEqual(data['name'], instance.name)
        self.assertIsNotNone(data['created'])
        self.assertIsNotNone(data['last_updated'])

