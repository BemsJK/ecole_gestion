from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.tableau_de_bord, name="tableau_de_bord"),
    path(
        "bulletin/<int:eleve_id>/<int:semestre_id>/",
        views.bulletin_eleve,
        name="bulletin_eleve",
    ),
]


