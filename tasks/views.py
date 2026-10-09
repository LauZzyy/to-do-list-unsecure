import hmac
import logging
import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html_join
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

from .forms import TaskForm
from .models import Task

logger = logging.getLogger(__name__)


def index(request):
    form = TaskForm()

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            logger.info("Tache ajoutee : id=%s", task.pk)
        return redirect("/")

    context = {
        "tasks": Task.objects.all(),
        "form": form,
        "welcome_message": "Bienvenue sur votre TO DO LIST !",
    }
    return render(request, "tasks/list.html", context)


def update_task(request, pk):
    task = get_object_or_404(Task, id=pk)
    form = TaskForm(instance=task)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            logger.info("Tache modifiee : id=%s", task.pk)
            return redirect("/")

    return render(request, "tasks/update_task.html", {"form": form})


def delete_task(request, pk):
    item = get_object_or_404(Task, id=pk)

    if request.method == "POST":
        item.delete()
        logger.info("Tache supprimee : id=%s", pk)
        next_url = request.GET.get("next", "/")
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = "/"
        return redirect(next_url)

    return render(request, "tasks/delete.html", {"item": item})


@require_GET
def search_tasks(request):
    query = request.GET.get("q", "")
    tasks = Task.objects.filter(title__icontains=query)
    items = format_html_join("", "<li>{}</li>", ((t.title,) for t in tasks))
    return HttpResponse("<ul>" + items + "</ul>")


@require_GET
def admin_panel(request):
    # Le mot de passe vient de l'environnement (fichier de secrets déployé par Ansible
    # depuis le Credentials Store de Jenkins) : il n'est plus dans le code.
    expected = os.environ.get("TODOLIST_ADMIN_PASSWORD", "")
    given = request.headers.get("X-Admin-Password", "")
    if expected and hmac.compare_digest(given.encode(), expected.encode()):
        return HttpResponse("Bienvenue admin !")
    return HttpResponse("Acces refuse", status=403)
