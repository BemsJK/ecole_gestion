from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404, render

from .models import (
    AnneeScolaire,
    Eleve,
    Evaluation,
    FraisScolaire,
    Matiere,
    Note,
    Paiement,
    Semestre,
)


def _get_annee_active() -> AnneeScolaire | None:
    return AnneeScolaire.objects.filter(active=True).order_by("-nom").first()


def tableau_de_bord(request):
    """
    Vue simple de tableau de bord :
    - nombre d'élèves
    - total encaissé
    - total dû (frais scolaires définis - paiements)
    """

    annee = _get_annee_active()

    if not annee:
        contexte = {
            "annee": None,
            "nb_eleves": 0,
            "total_frais": Decimal("0.00"),
            "total_paye": Decimal("0.00"),
            "reste_a_payer": Decimal("0.00"),
            "eleves_impayes": [],
        }
        return render(request, "gestion/tableau_de_bord.html", contexte)

    eleves = Eleve.objects.filter(annee_scolaire=annee, actif=True)
    nb_eleves = eleves.count()

    total_frais_par_eleve = (
        FraisScolaire.objects.filter(annee_scolaire=annee)
        .aggregate(total=Sum("montant"))
        .get("total")
        or Decimal("0.00")
    )
    total_frais = total_frais_par_eleve * nb_eleves

    total_paye = (
        Paiement.objects.filter(annee_scolaire=annee)
        .aggregate(total=Sum("montant_paye"))
        .get("total")
        or Decimal("0.00")
    )

    reste_a_payer = total_frais - total_paye

    # Détail par élève pour savoir qui n'a pas tout payé
    montants_payes_par_eleve = (
        Paiement.objects.filter(annee_scolaire=annee)
        .values("eleve_id")
        .annotate(total=Sum("montant_paye"))
    )
    paye_par_eleve = {row["eleve_id"]: row["total"] for row in montants_payes_par_eleve}

    eleves_impayes = []
    for eleve in eleves:
        paye = paye_par_eleve.get(eleve.id, Decimal("0.00"))
        reste = total_frais_par_eleve - paye
        if reste > 0:
            eleves_impayes.append(
                {
                    "eleve": eleve,
                    "paye": paye,
                    "reste": reste,
                    "total_frais": total_frais_par_eleve,
                }
            )

    contexte = {
        "annee": annee,
        "nb_eleves": nb_eleves,
        "total_frais": total_frais,
        "total_paye": total_paye,
        "reste_a_payer": reste_a_payer,
        "eleves_impayes": eleves_impayes,
    }
    return render(request, "gestion/tableau_de_bord.html", contexte)


def bulletin_eleve(request, eleve_id: int, semestre_id: int):
    """
    Génération d'un bulletin simple pour un élève et un semestre.
    """

    eleve = get_object_or_404(Eleve, pk=eleve_id)
    semestre = get_object_or_404(Semestre, pk=semestre_id)

    # Récupérer toutes les matières de la classe de l'élève
    matieres = Matiere.objects.filter(classe=eleve.classe).order_by("nom")

    lignes_bulletin = []
    total_points = Decimal("0.00")
    total_coeffs = Decimal("0.00")

    for matiere in matieres:
        evaluations = Evaluation.objects.filter(
            matiere=matiere, semestre=semestre
        ).order_by("date")
        notes = Note.objects.filter(
            eleve=eleve, evaluation__in=evaluations
        ).select_related("evaluation")

        if not notes:
            moyenne_matiere = None
        else:
            somme = Decimal("0.00")
            somme_coeffs = Decimal("0.00")
            for note in notes:
                coeff = Decimal(note.evaluation.coefficient)
                somme += Decimal(note.valeur) * coeff
                somme_coeffs += coeff
            moyenne_matiere = somme / somme_coeffs if somme_coeffs > 0 else None

            if moyenne_matiere is not None:
                total_points += moyenne_matiere * Decimal(matiere.coefficient)
                total_coeffs += Decimal(matiere.coefficient)

        lignes_bulletin.append(
            {
                "matiere": matiere,
                "notes": notes,
                "moyenne": moyenne_matiere,
            }
        )

    moyenne_generale = (
        total_points / total_coeffs if total_coeffs > 0 else None
    )

    contexte = {
        "eleve": eleve,
        "semestre": semestre,
        "lignes_bulletin": lignes_bulletin,
        "moyenne_generale": moyenne_generale,
    }
    return render(request, "gestion/bulletin_eleve.html", contexte)

