"""Vues budget mensuel / annuel de la flotte."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import ActionTraceur
from .forms import BudgetFlotteForm, AchatDocumentBordForm
from .models import BudgetFlotte, AchatDocumentBord


def is_admin_or_dispatch_or_superuser(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) in ('admin', 'dispatch') or user.is_superuser
    )


def _budgets_qs(user):
    qs = BudgetFlotte.objects.select_related('etablissement', 'createur')
    if not user.is_superuser and getattr(user, 'etablissement', None):
        qs = qs.filter(etablissement=user.etablissement)
    return qs


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def liste_budgets(request):
    budgets = _budgets_qs(request.user)
    annee = request.GET.get('annee')
    periode = request.GET.get('periode')
    if annee:
        budgets = budgets.filter(annee=annee)
    if periode in ('mensuel', 'annuel'):
        budgets = budgets.filter(periode_type=periode)

    rows = []
    for b in budgets:
        suivi = b.suivi()
        rows.append({'budget': b, 'suivi': suivi})

    return render(request, 'rapport/liste_budgets.html', {
        'rows': rows,
        'filtre_annee': annee or '',
        'filtre_periode': periode or '',
        'annee_courante': timezone.localdate().year,
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def creer_budget(request):
    if request.method == 'POST':
        form = BudgetFlotteForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                budget = form.save()
                ActionTraceur.objects.create(
                    utilisateur=request.user,
                    action="Création budget flotte",
                    details=str(budget),
                )
                messages.success(request, f"Budget enregistré : {budget}")
                return redirect('rapport:detail_budget', budget_id=budget.id)
            except Exception as e:
                messages.error(request, f"Impossible d'enregistrer (période déjà budgétée ?) : {e}")
    else:
        form = BudgetFlotteForm(user=request.user)

    return render(request, 'rapport/formulaire_budget.html', {
        'form': form,
        'title': 'Nouveau budget flotte',
        'mode': 'create',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def modifier_budget(request, budget_id):
    budget = get_object_or_404(_budgets_qs(request.user), pk=budget_id)
    if request.method == 'POST':
        form = BudgetFlotteForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            try:
                budget = form.save()
                messages.success(request, "Budget mis à jour.")
                return redirect('rapport:detail_budget', budget_id=budget.id)
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
    else:
        form = BudgetFlotteForm(instance=budget, user=request.user)

    return render(request, 'rapport/formulaire_budget.html', {
        'form': form,
        'title': f'Modifier — {budget}',
        'budget': budget,
        'mode': 'edit',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def detail_budget(request, budget_id):
    budget = get_object_or_404(_budgets_qs(request.user), pk=budget_id)
    suivi = budget.suivi()
    debut, fin = budget.periode_dates()
    return render(request, 'rapport/detail_budget.html', {
        'budget': budget,
        'suivi': suivi,
        'date_debut': debut,
        'date_fin': fin,
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def supprimer_budget(request, budget_id):
    budget = get_object_or_404(_budgets_qs(request.user), pk=budget_id)
    if request.method == 'POST':
        label = str(budget)
        budget.delete()
        messages.success(request, f"Budget supprimé : {label}")
        return redirect('rapport:liste_budgets')
    return render(request, 'rapport/confirmer_suppression_budget.html', {'budget': budget})


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def liste_achats_documents(request):
    qs = AchatDocumentBord.objects.select_related('vehicule', 'etablissement', 'createur')
    if not request.user.is_superuser and getattr(request.user, 'etablissement', None):
        qs = qs.filter(etablissement=request.user.etablissement)
    return render(request, 'rapport/liste_achats_documents.html', {
        'achats': qs[:200],
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def creer_achat_document(request):
    if request.method == 'POST':
        form = AchatDocumentBordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            achat = form.save()
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action="Achat document de bord",
                details=str(achat),
            )
            messages.success(request, f"Achat enregistré : {achat}")
            return redirect('rapport:liste_achats_documents')
    else:
        form = AchatDocumentBordForm(user=request.user)
    return render(request, 'rapport/formulaire_achat_document.html', {
        'form': form,
        'title': 'Enregistrer un achat de document de bord',
    })
