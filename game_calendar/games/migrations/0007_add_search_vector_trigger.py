from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_game_search_vector_game_summary_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION update_game_search_vector() RETURNS trigger AS $$
            BEGIN
              NEW.search_vector := setweight(to_tsvector('english', NEW.title), 'A') || setweight(to_tsvector('english', NEW.summary), 'B');
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER game_search_vector_update
            BEFORE INSERT OR UPDATE ON games_game
            FOR EACH ROW EXECUTE FUNCTION update_game_search_vector();
            """,
            """
            DROP TRIGGER IF EXISTS game_search_vector_update ON games_game;
            DROP FUNCTION IF EXISTS update_game_search_vector();
            """
        ),
    ]