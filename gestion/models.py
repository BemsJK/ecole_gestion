from django.db import models
from django.utils import timezone


class AnneeScolaire(models.Model):
    """
    Exemple : 2025-2026
    """

    nom = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "année scolaire"
        verbose_name_plural = "années scolaires"

    def __str__(self) -> str:
        return self.nom


class Classe(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    niveau = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "classe"
        verbose_name_plural = "classes"
        ordering = ["nom"]

    def __str__(self) -> str:
        return self.nom


class Semestre(models.Model):
    """
    Semestre 1 / Semestre 2, lié à une année scolaire.
    """

    annee_scolaire = models.ForeignKey(
        AnneeScolaire, on_delete=models.CASCADE, related_name="semestres"
    )
    nom = models.CharField(max_length=50)
    ordre = models.PositiveIntegerField(help_text="Ordre d'affichage (1, 2, ...)")

    class Meta:
        verbose_name = "semestre"
        verbose_name_plural = "semestres"
        unique_together = ("annee_scolaire", "nom")
        ordering = ["annee_scolaire__nom", "ordre"]

    def __str__(self) -> str:
        return f"{self.annee_scolaire} - {self.nom}"


class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    classe = models.ForeignKey(
        Classe,
        on_delete=models.CASCADE,
        related_name="matieres",
        help_text="Classe principale pour cette matière",
    )

    class Meta:
        verbose_name = "matière"
        verbose_name_plural = "matières"
        unique_together = ("nom", "classe")
        ordering = ["classe__nom", "nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.classe})"


class Enseignant(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    matieres = models.ManyToManyField(Matiere, blank=True, related_name="enseignants")

    class Meta:
        verbose_name = "enseignant"
        verbose_name_plural = "enseignants"
        ordering = ["nom", "prenom"]

    def __str__(self) -> str:
        return f"{self.nom} {self.prenom}".strip()


class Eleve(models.Model):
    """
    Élève avec un matricule généré automatiquement.
    """

    matricule = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Généré automatiquement à l'enregistrement",
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone_parent = models.CharField(max_length=30, blank=True)
    email_parent = models.EmailField(blank=True)
    classe = models.ForeignKey(
        Classe, on_delete=models.PROTECT, related_name="eleves", null=True, blank=True
    )
    annee_scolaire = models.ForeignKey(
        AnneeScolaire,
        on_delete=models.PROTECT,
        related_name="eleves",
        null=True,
        blank=True,
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "élève"
        verbose_name_plural = "élèves"
        ordering = ["nom", "prenom"]

    def __str__(self) -> str:
        return f"{self.matricule} - {self.nom} {self.prenom}".strip()

    def save(self, *args, **kwargs):
        if not self.matricule:
            year = timezone.now().year
            prefix = f"{year}-"
            last_eleve = (
                Eleve.objects.filter(matricule__startswith=prefix)
                .order_by("-id")
                .first()
            )
            if last_eleve and "-" in last_eleve.matricule:
                try:
                    last_number = int(last_eleve.matricule.split("-")[-1])
                except ValueError:
                    last_number = 0
            else:
                last_number = 0
            self.matricule = f"{prefix}{last_number + 1:04d}"
        super().save(*args, **kwargs)


class Evaluation(models.Model):
    """
    Contrôle, devoir, examen...
    """

    TYPE_CHOICES = [
        ("CONTROLE", "Contrôle"),
        ("DEVOIR", "Devoir"),
        ("EXAMEN", "Examen"),
    ]

    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE, related_name="evaluations"
    )
    semestre = models.ForeignKey(
        Semestre, on_delete=models.CASCADE, related_name="evaluations"
    )
    date = models.DateField(default=timezone.now)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "évaluation"
        verbose_name_plural = "évaluations"
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.matiere} - {self.get_type_display()} ({self.date})"


class Note(models.Model):
    eleve = models.ForeignKey(
        Eleve, on_delete=models.CASCADE, related_name="notes"
    )
    evaluation = models.ForeignKey(
        Evaluation, on_delete=models.CASCADE, related_name="notes"
    )
    valeur = models.DecimalField(max_digits=5, decimal_places=2)
    remarque = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "note"
        verbose_name_plural = "notes"
        unique_together = ("eleve", "evaluation")

    def __str__(self) -> str:
        return f"{self.eleve} - {self.evaluation} : {self.valeur}"


class FraisScolaire(models.Model):
    """
    Type de frais : inscription, mensualité, transport, etc.
    """

    annee_scolaire = models.ForeignKey(
        AnneeScolaire, on_delete=models.CASCADE, related_name="frais"
    )
    libelle = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    obligatoire = models.BooleanField(default=True)

    class Meta:
        verbose_name = "frais scolaire"
        verbose_name_plural = "frais scolaires"
        unique_together = ("annee_scolaire", "libelle")
        ordering = ["annee_scolaire__nom", "libelle"]

    def __str__(self) -> str:
        return f"{self.libelle} ({self.annee_scolaire})"


class Paiement(models.Model):
    MODE_CHOICES = [
        ("ESPECES", "Espèces"),
        ("MOBILE_MONEY", "Mobile money"),
        ("VIREMENT", "Virement bancaire"),
        ("CHEQUE", "Chèque"),
    ]

    MOIS_CHOICES = [
        (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
        (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
        (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
    ]

    eleve = models.ForeignKey(
        Eleve, on_delete=models.CASCADE, related_name="paiements"
    )
    mois = models.PositiveSmallIntegerField(
        choices=MOIS_CHOICES,
        null=True,
        blank=True,
        help_text="Mois concerné par ce paiement (mensualité).",
    )
    annee_scolaire = models.ForeignKey(
        AnneeScolaire,
        on_delete=models.PROTECT,
        related_name="paiements",
        null=True,
        blank=True,
        help_text="Année scolaire concernée.",
    )
    date_paiement = models.DateField(default=timezone.now)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="ESPECES")
    reference = models.CharField(
        max_length=100, blank=True, help_text="Référence du reçu / transaction"
    )
    remarque = models.CharField(max_length=255, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "paiement"
        verbose_name_plural = "paiements"
        ordering = ["-date_paiement"]

    def __str__(self) -> str:
        return f"{self.eleve} - {self.get_mois_display()} {self.annee_scolaire} : {self.montant_paye} le {self.date_paiement}"


# --- Paramètres généraux (délai de rappel impayés, etc.) ---


class ParametreEcole(models.Model):
    """
    Paramètres globaux (une seule ligne en base).
    Délai en jours après la date limite de paiement avant de notifier l'admin.
    """

    delai_jours_rappel_impayes = models.PositiveIntegerField(
        default=3,
        help_text="Nombre de jours après la date limite pour notifier les mensualités impayées.",
    )

    class Meta:
        verbose_name = "paramètre école"
        verbose_name_plural = "paramètres école"

    def __str__(self) -> str:
        return f"Rappel impayés après {self.delai_jours_rappel_impayes} jours"

    def save(self, *args, **kwargs):
        # On ne garde qu'une seule ligne (singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"delai_jours_rappel_impayes": 3})
        return obj


# --- Mensualités : un mois = une période, payé ou pas par élève ---


class PeriodeMensuelle(models.Model):
    """
    Une période mensuelle (ex. Janvier 2026) pour le suivi des paiements.
    date_limite = date jusqu'à laquelle la mensualité doit être payée (ex. 5 du mois suivant).
    """

    MOIS_NOMS = [
        (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
        (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
        (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
    ]

    annee_scolaire = models.ForeignKey(
        AnneeScolaire, on_delete=models.CASCADE, related_name="periodes_mensuelles"
    )
    mois = models.PositiveSmallIntegerField(choices=MOIS_NOMS)  # 1-12
    annee = models.PositiveIntegerField()  # ex. 2026
    date_limite = models.DateField(
        help_text="Date limite de paiement (ex. 5 du mois suivant)."
    )

    class Meta:
        verbose_name = "période mensuelle"
        verbose_name_plural = "périodes mensuelles"
        unique_together = ("annee_scolaire", "mois", "annee")
        ordering = ["annee_scolaire", "annee", "mois"]

    def __str__(self) -> str:
        return f"{self.get_mois_display()} {self.annee} (échéance {self.date_limite})"


class ReglementMensuel(models.Model):
    """
    Pour chaque élève et chaque période mensuelle : payé ou pas.
    On peut cocher "payé" et optionnellement lier à un paiement (compta).
    """

    eleve = models.ForeignKey(
        Eleve, on_delete=models.CASCADE, related_name="reglements_mensuels"
    )
    periode = models.ForeignKey(
        PeriodeMensuelle, on_delete=models.CASCADE, related_name="reglements"
    )
    paye = models.BooleanField(default=False, verbose_name="Payé")
    date_paiement = models.DateField(null=True, blank=True)
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reglement_mensuel",
        help_text="Lien optionnel vers le paiement (compta).",
    )

    class Meta:
        verbose_name = "règlement mensuel"
        verbose_name_plural = "règlements mensuels"
        unique_together = ("eleve", "periode")
        ordering = ["-periode__annee", "-periode__mois", "eleve__nom"]

    def __str__(self) -> str:
        return f"{self.eleve} - {self.periode} : {'Payé' if self.paye else 'Impayé'}"

