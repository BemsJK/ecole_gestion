from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from . import models


@admin.register(models.AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    search_fields = ['nom', 'date_debut']  # ajoute les champs pertinents
    list_display = ("nom", "active")
    list_filter = ("active",)


class EleveInline(admin.TabularInline):
    model = models.Eleve
    fk_name = "classe"
    extra = 0
    fields = ("matricule", "nom", "prenom", "date_naissance", "telephone_parent", "email_parent", "annee_scolaire", "actif")
    readonly_fields = ("matricule",)
    show_change_link = True


@admin.register(models.Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ("nom", "niveau")
    search_fields = ("nom", "niveau")
    inlines = [EleveInline]


@admin.register(models.Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display = ("nom", "annee_scolaire", "ordre")
    list_filter = ("annee_scolaire",)
    ordering = ("annee_scolaire__nom", "ordre")


@admin.register(models.Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ("nom", "classe", "coefficient", "enseignants_list")
    list_filter = ("classe",)
    search_fields = ("nom",)
    readonly_fields = ("enseignants_list",)
    fieldsets = (
        (None, {"fields": ("nom", "classe", "coefficient")}),
        ("Enseignants assignés", {"fields": ("enseignants_list",)}),
    )

    def enseignants_list(self, obj):
        if obj.pk:
            enseignants = obj.enseignants.all()
            if enseignants:
                return mark_safe(
                    "<ul>"
                    + "".join(f"<li>{e.nom} {e.prenom} — {e.email or '—'} — {e.telephone or '—'}</li>" for e in enseignants)
                    + "</ul>"
                )
            return "Aucun enseignant assigné"
        return "—"
    enseignants_list.short_description = "Enseignants assignés"


@admin.register(models.Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "email", "telephone")
    search_fields = ("nom", "prenom", "email", "telephone")
    filter_horizontal = ("matieres",)


@admin.register(models.Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = (
        "matricule",
        "nom",
        "prenom",
        "classe",
        "annee_scolaire",
        "actif",
    )
    list_filter = ("classe", "annee_scolaire", "actif")
    search_fields = ("matricule", "nom", "prenom", "telephone_parent", "email_parent")


@admin.register(models.Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("matiere", "semestre", "type", "date", "coefficient")
    list_filter = ("semestre", "matiere", "type")
    search_fields = ("description",)


@admin.register(models.Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("eleve", "evaluation", "valeur")
    list_filter = ("evaluation__semestre", "evaluation__matiere")
    search_fields = ("eleve__nom", "eleve__prenom", "evaluation__description")


@admin.register(models.FraisScolaire)
class FraisScolaireAdmin(admin.ModelAdmin):
    list_display = ("libelle", "annee_scolaire", "montant", "obligatoire")
    list_filter = ("annee_scolaire", "obligatoire")
    search_fields = ("libelle",)


@admin.register(models.Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "eleve",
        "mois",
        "annee_scolaire",
        "montant_paye",
        "date_paiement",
        "mode",
        "reference",
    )
    list_filter = ("mois", "annee_scolaire", "mode", "date_paiement")
    search_fields = ("eleve__nom", "eleve__prenom", "reference")
    autocomplete_fields = ("eleve", "annee_scolaire")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Rendre mois et annee_scolaire obligatoires pour les nouveaux paiements
        if "mois" in form.base_fields:
            form.base_fields["mois"].required = True
        if "annee_scolaire" in form.base_fields:
            form.base_fields["annee_scolaire"].required = True
        return form


# --- Paramètres école (délai de rappel impayés) ---


@admin.register(models.ParametreEcole)
class ParametreEcoleAdmin(admin.ModelAdmin):
    list_display = ("delai_jours_rappel_impayes",)

    def has_add_permission(self, request):
        return not models.ParametreEcole.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# --- Périodes mensuelles et règlements (payé / pas payé) ---


@admin.register(models.PeriodeMensuelle)
class PeriodeMensuelleAdmin(admin.ModelAdmin):
    list_display = ("annee_scolaire", "mois", "annee", "date_limite")
    list_filter = ("annee_scolaire", "annee")
    ordering = ("-annee", "-mois")

    actions = ["creer_reglements_manquants"]

    @admin.action(description="Créer les règlements manquants pour cette période")
    def creer_reglements_manquants(self, request, queryset):
        created = 0
        for periode in queryset:
            annee = periode.annee_scolaire
            eleves = models.Eleve.objects.filter(
                annee_scolaire=annee, actif=True
            ).exclude(reglements_mensuels__periode=periode)
            for eleve in eleves:
                models.ReglementMensuel.objects.get_or_create(
                    eleve=eleve, periode=periode, defaults={"paye": False}
                )
                created += 1
        self.message_user(request, f"{created} règlement(s) créé(s).")


@admin.register(models.ReglementMensuel)
class ReglementMensuelAdmin(admin.ModelAdmin):
    list_display = ("eleve", "periode", "paye", "date_paiement", "paiement")
    list_editable = ("paye",)
    list_filter = ("paye", "periode__annee_scolaire", "periode")
    search_fields = ("eleve__nom", "eleve__prenom", "eleve__matricule")
    ordering = ("-periode__annee", "-periode__mois", "eleve__nom")
    list_per_page = 50

    def save_model(self, request, obj, form, change):
        if obj.paye and not obj.date_paiement:
            obj.date_paiement = timezone.now().date()
        super().save_model(request, obj, form, change)
