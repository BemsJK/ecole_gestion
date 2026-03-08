"""
Calcul des alertes impayés (mensualités en retard) pour notification admin.
"""
from datetime import timedelta

from django.utils import timezone

from .models import ParametreEcole, PeriodeMensuelle, ReglementMensuel


def get_alertes_impayes():
    """Retourne la liste des règlements mensuels impayés (échéance + délai dépassés)."""
    try:
        params = ParametreEcole.load()
        today = timezone.now().date()
        seuil = today - timedelta(days=params.delai_jours_rappel_impayes)
        periodes_en_retard = PeriodeMensuelle.objects.filter(date_limite__lte=seuil)
        return list(
            ReglementMensuel.objects.filter(
                periode__in=periodes_en_retard, paye=False
            )
            .select_related("eleve", "periode", "periode__annee_scolaire")[:50]
        )
    except Exception:
        return []
