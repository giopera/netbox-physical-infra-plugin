from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_physical_infra_plugin', '0003_remove_junctionbox_terminals_down_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conduit',
            name='end_position',
        ),
        migrations.RemoveField(
            model_name='conduit',
            name='start_position',
        ),
    ]
