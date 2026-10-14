from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_order_khqr_order_md5_order_qr_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='telegram_notification_sent',
            field=models.BooleanField(
                default=False,
                verbose_name='telegram notification sent',
                help_text='Set to true once the order success Telegram notification has been sent.'
            ),
        ),
    ]
