"""The access log is append-only, enforced by Postgres rather than by app discipline.

A superuser can still drop the trigger; this stops app bugs and careless migrations.
"""

from django.db import migrations

FORWARD = """
CREATE FUNCTION core_accesslog_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'core_accesslog is append-only';
END $$;
CREATE TRIGGER core_accesslog_no_change BEFORE UPDATE OR DELETE ON core_accesslog
    FOR EACH ROW EXECUTE FUNCTION core_accesslog_append_only();
CREATE TRIGGER core_accesslog_no_truncate BEFORE TRUNCATE ON core_accesslog
    FOR EACH STATEMENT EXECUTE FUNCTION core_accesslog_append_only();
"""

REVERSE = """
DROP TRIGGER core_accesslog_no_truncate ON core_accesslog;
DROP TRIGGER core_accesslog_no_change ON core_accesslog;
DROP FUNCTION core_accesslog_append_only();
"""


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [migrations.RunSQL(FORWARD, REVERSE)]
