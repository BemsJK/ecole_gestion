"""
Notification des mensualités impayées à la connexion admin.
"""
from django.contrib import messages
from django.utils.safestring import mark_safe

from .admin_site import get_alertes_impayes


class NotificationImpayesMiddleware:
    """
    À chaque requête vers l'admin, si l'utilisateur est connecté et staff,
    affiche un message d'alerte s'il y a des mensualités impayées (échéance + délai dépassés).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Notification uniquement sur la page d'accueil admin (à chaque « connexion »)
        if (
            request.path.rstrip("/") == "/admin"
            and request.user.is_authenticated
            and request.user.is_staff
        ):
            alertes = get_alertes_impayes()
            if alertes:
                url = "/admin/gestion/reglementmensuel/?paye__exact=0"
                msg = mark_safe(
                    f'<strong>⚠️ {len(alertes)} mensualité(s) impayée(s)</strong> '
                    f'(échéance dépassée). '
                    f'<a href="{url}">Voir les règlements mensuels</a>'
                )
                messages.warning(request, msg)

        return self.get_response(request)
