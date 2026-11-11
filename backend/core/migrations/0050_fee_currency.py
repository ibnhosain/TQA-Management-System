from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_easy_qaida_new_books'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fee_currency',
            field=models.CharField(
                choices=[('BDT', '৳ টাকা'), ('USD', '$ ডলার')],
                default='BDT',
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name='feepayment',
            name='currency',
            field=models.CharField(default='BDT', max_length=3),
        ),
    ]
