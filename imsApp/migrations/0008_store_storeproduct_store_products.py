# Generated by Django 4.0.3 on 2023-02-17 15:09

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('imsApp', '0007_invoice_date_created_invoice_date_updated'),
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('address', models.TextField()),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='imsApp.category')),
            ],
        ),
        migrations.CreateModel(
            name='StoreProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='imsApp.product')),
                ('stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='imsApp.stock')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='imsApp.store')),
            ],
        ),
        migrations.AddField(
            model_name='store',
            name='products',
            field=models.ManyToManyField(through='imsApp.StoreProduct', to='imsApp.product'),
        ),
    ]
