from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_fee_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecturetopic',
            name='today_plan',
            field=models.BooleanField(default=False, verbose_name='আজকের পাঠে আছে'),
        ),
    ]
