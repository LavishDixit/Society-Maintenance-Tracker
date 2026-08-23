from django.db import migrations


def migrate_role_forward(apps, schema_editor):
    """Anyone who was 'admin' under the old exclusive role system becomes
    a committee member under the new additive permission flag, so nobody
    loses admin access during the upgrade."""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='admin').update(is_committee=True)


def migrate_role_backward(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_committee=True).update(role='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_options_user_is_committee_user_wing_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_role_forward, migrate_role_backward),
    ]
