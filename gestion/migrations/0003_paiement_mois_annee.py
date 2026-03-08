# Generated manually for transition frais -> mois + annee_scolaire

from django.db import migrations, models
import django.db.models.deletion


def migrer_paiements(apps, schema_editor):
    """Remplir mois et annee_scolaire à partir de frais et date_paiement."""
    Paiement = apps.get_model("gestion", "Paiement")
    AnneeScolaire = apps.get_model("gestion", "AnneeScolaire")
    for p in Paiement.objects.select_related("frais").all():
        p.mois = p.date_paiement.month
        if p.frais_id:
            p.annee_scolaire_id = p.frais.annee_scolaire_id
        else:
            first = AnneeScolaire.objects.first()
            p.annee_scolaire_id = first.id if first else None
        p.save()


def reverse_migrer(apps, schema_editor):
    pass  # Pas de retour possible


class Migration(migrations.Migration):

    dependencies = [
        ("gestion", "0002_parametreecole_periodemensuelle_reglementmensuel"),
    ]

    operations = [
        migrations.AddField(
            model_name="paiement",
            name="mois",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Janvier"),
                    (2, "Février"),
                    (3, "Mars"),
                    (4, "Avril"),
                    (5, "Mai"),
                    (6, "Juin"),
                    (7, "Juillet"),
                    (8, "Août"),
                    (9, "Septembre"),
                    (10, "Octobre"),
                    (11, "Novembre"),
                    (12, "Décembre"),
                ],
                help_text="Mois concerné par ce paiement (mensualité).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="paiement",
            name="annee_scolaire",
            field=models.ForeignKey(
                blank=True,
                help_text="Année scolaire concernée.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="paiements",
                to="gestion.anneescolaire",
            ),
        ),
        migrations.RunPython(migrer_paiements, reverse_migrer),
        migrations.RemoveField(
            model_name="paiement",
            name="frais",
        ),
    ]
