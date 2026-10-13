from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0010_alter_booking_service_alter_booking_specialist"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS btree_gist;

                ALTER TABLE bookings_booking
                ADD CONSTRAINT booking_no_overlapping_scheduled_slots
                EXCLUDE USING GIST (
                    specialist_id WITH =,
                    tsrange(
                        date + time,
                        date + time
                            + service_duration * interval '1 minute',
                        '[)'
                    ) WITH &&
                )
                WHERE (status = 'scheduled');
            """,
            reverse_sql="""
                ALTER TABLE bookings_booking
                DROP CONSTRAINT IF EXISTS
                booking_no_overlapping_scheduled_slots;
            """,
        ),
    ]
