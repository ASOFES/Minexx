"""
Répare l'état partiel de securite.0002 / entretien.0005 sur PostgreSQL (Railway).
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_vehicules.settings")
django.setup()

from django.core.management import call_command
from django.db import connection
from django.utils import timezone


def q(sql, params=None):
    with connection.cursor() as c:
        c.execute(sql, params or [])
        try:
            return c.fetchall()
        except Exception:
            return []


def column_exists(table, column):
    rows = q(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name=%s AND column_name=%s
        """,
        [table, column],
    )
    return bool(rows)


def table_exists(table):
    rows = q("SELECT to_regclass(%s)", [table])
    return bool(rows and rows[0][0])


def migration_applied(app, name):
    rows = q(
        "SELECT 1 FROM django_migrations WHERE app=%s AND name=%s",
        [app, name],
    )
    return bool(rows)


def main():
    print("=== Fix incident dossier migrations ===")

    with connection.cursor() as c:
        c.execute('DROP INDEX IF EXISTS "securite_incidentsecurite_numero_dossier_447e482f_like"')
        c.execute('DROP INDEX IF EXISTS "securite_incidentsecurite_numero_dossier_447e482f"')
        print("Orphan indexes dropped (if existed)")

        # Colonnes incident
        alters = []
        if not column_exists("securite_incidentsecurite", "numero_dossier"):
            alters.append(
                'ADD COLUMN "numero_dossier" varchar(32) NULL'
            )
        if not column_exists("securite_incidentsecurite", "date_modification"):
            alters.append(
                'ADD COLUMN "date_modification" timestamp with time zone NULL'
            )
        if not column_exists("securite_incidentsecurite", "date_traitement"):
            alters.append('ADD COLUMN "date_traitement" timestamp with time zone NULL')
        if not column_exists("securite_incidentsecurite", "date_cloture"):
            alters.append('ADD COLUMN "date_cloture" timestamp with time zone NULL')
        if not column_exists("securite_incidentsecurite", "traite_par_id"):
            alters.append('ADD COLUMN "traite_par_id" integer NULL')
        if not column_exists("securite_incidentsecurite", "clos_par_id"):
            alters.append('ADD COLUMN "clos_par_id" integer NULL')

        for stmt in alters:
            sql = f'ALTER TABLE "securite_incidentsecurite" {stmt}'
            print("SQL:", sql)
            c.execute(sql)

        # Fill date_modification
        if column_exists("securite_incidentsecurite", "date_modification"):
            c.execute(
                """
                UPDATE securite_incidentsecurite
                SET date_modification = COALESCE(date_modification, date_signalement, NOW())
                WHERE date_modification IS NULL
                """
            )

        # Populate numero_dossier
        if column_exists("securite_incidentsecurite", "numero_dossier"):
            c.execute(
                """
                SELECT id, date_signalement FROM securite_incidentsecurite
                WHERE numero_dossier IS NULL OR numero_dossier = ''
                ORDER BY id
                """
            )
            rows = c.fetchall()
            for incident_id, dt in rows:
                day = (dt.date() if dt else timezone.localdate()).strftime("%Y%m%d")
                prefix = f"INC-{day}-"
                c.execute(
                    """
                    SELECT COUNT(*) FROM securite_incidentsecurite
                    WHERE numero_dossier LIKE %s
                    """,
                    [prefix + "%"],
                )
                seq = c.fetchone()[0] + 1
                while True:
                    candidate = f"{prefix}{seq:04d}"
                    c.execute(
                        "SELECT 1 FROM securite_incidentsecurite WHERE numero_dossier=%s",
                        [candidate],
                    )
                    if not c.fetchone():
                        break
                    seq += 1
                c.execute(
                    "UPDATE securite_incidentsecurite SET numero_dossier=%s WHERE id=%s",
                    [candidate, incident_id],
                )
                print("Assigned", candidate, "to incident", incident_id)

        # Unique index on numero_dossier
        c.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS securite_incidentsecurite_numero_dossier_key
            ON securite_incidentsecurite (numero_dossier)
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS securite_incidentsecurite_numero_dossier_447e482f
            ON securite_incidentsecurite (numero_dossier)
            """
        )

        # Photo table
        if not table_exists("securite_photoincidentsecurite"):
            print("Creating securite_photoincidentsecurite")
            c.execute(
                """
                CREATE TABLE securite_photoincidentsecurite (
                    id bigserial PRIMARY KEY,
                    image varchar(100) NOT NULL,
                    legende varchar(255) NOT NULL DEFAULT '',
                    date_ajout timestamp with time zone NOT NULL DEFAULT NOW(),
                    incident_id integer NOT NULL
                        REFERENCES securite_incidentsecurite(id) DEFERRABLE INITIALLY DEFERRED
                )
                """
            )
            c.execute(
                """
                CREATE INDEX securite_photoincidentsecurite_incident_id
                ON securite_photoincidentsecurite (incident_id)
                """
            )

        # FKs traite_par / clos_par
        c.execute(
            """
            DO $$ BEGIN
                ALTER TABLE securite_incidentsecurite
                ADD CONSTRAINT securite_incidentsecurite_traite_par_id_fk
                FOREIGN KEY (traite_par_id) REFERENCES core_utilisateur(id)
                DEFERRABLE INITIALLY DEFERRED;
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
            """
        )
        c.execute(
            """
            DO $$ BEGIN
                ALTER TABLE securite_incidentsecurite
                ADD CONSTRAINT securite_incidentsecurite_clos_par_id_fk
                FOREIGN KEY (clos_par_id) REFERENCES core_utilisateur(id)
                DEFERRABLE INITIALLY DEFERRED;
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
            """
        )

        # entretien columns
        if table_exists("entretien_reparationmecanique"):
            if not column_exists("entretien_reparationmecanique", "numero_dossier"):
                c.execute(
                    'ALTER TABLE entretien_reparationmecanique ADD COLUMN "numero_dossier" varchar(32) NOT NULL DEFAULT \'\''
                )
                print("Added entretien.numero_dossier")
            if not column_exists("entretien_reparationmecanique", "incident_id"):
                c.execute(
                    'ALTER TABLE entretien_reparationmecanique ADD COLUMN "incident_id" integer NULL'
                )
                c.execute(
                    """
                    DO $$ BEGIN
                        ALTER TABLE entretien_reparationmecanique
                        ADD CONSTRAINT entretien_reparationmecanique_incident_id_fk
                        FOREIGN KEY (incident_id) REFERENCES securite_incidentsecurite(id)
                        DEFERRABLE INITIALLY DEFERRED;
                    EXCEPTION WHEN duplicate_object THEN NULL;
                    END $$;
                    """
                )
                print("Added entretien.incident_id")
            c.execute(
                """
                CREATE INDEX IF NOT EXISTS entretien_reparationmecanique_numero_dossier_idx
                ON entretien_reparationmecanique (numero_dossier)
                """
            )
            c.execute(
                """
                CREATE INDEX IF NOT EXISTS entretien_reparationmecanique_incident_id_idx
                ON entretien_reparationmecanique (incident_id)
                """
            )

    # Fake migrations if schema is ready
    if column_exists("securite_incidentsecurite", "numero_dossier") and table_exists(
        "securite_photoincidentsecurite"
    ):
        if not migration_applied("securite", "0002_dossier_incident_photos_lien_reparation"):
            print("Faking securite.0002…")
            call_command(
                "migrate",
                "securite",
                "0002_dossier_incident_photos_lien_reparation",
                fake=True,
                interactive=False,
            )

    if column_exists("entretien_reparationmecanique", "incident_id"):
        if not migration_applied("entretien", "0005_dossier_incident_photos_lien_reparation"):
            print("Faking entretien.0005…")
            call_command(
                "migrate",
                "entretien",
                "0005_dossier_incident_photos_lien_reparation",
                fake=True,
                interactive=False,
            )

    call_command("migrate", interactive=False)
    print(
        "VERIFY numero_dossier:",
        column_exists("securite_incidentsecurite", "numero_dossier"),
    )
    print("Done.")


if __name__ == "__main__":
    main()
