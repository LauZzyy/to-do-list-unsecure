import random
import hashlib
import subprocess
import yaml
import pickle
import base64

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import *
from .forms import *

# TODO: mettre en place une authentification utilisateur avant la mise en production
# FIXME: aucune validation des droits d'accès n'est présente dans les vues
# TODO: remplacer tous les appels print() par le module logging

# TODO: ne jamais stocker un mot de passe en clair dans le code source
ADMIN_PASSWORD = "Sup3rS3cret!123"


def generate_token(user_id):
    # TODO: random n'est pas cryptographiquement sûr, utiliser le module secrets
    return random.random()


def hash_password(password):
    # TODO: MD5 est cassé, utiliser bcrypt ou argon2 pour hasher les mots de passe
    return hashlib.md5(password.encode()).hexdigest()


def load_config(path="config.yaml"):
    with open(path) as f:
        # TODO: yaml.load sans Loader permet l'exécution de code arbitraire (CVE-2020-14343)
        return yaml.load(f.read())


def notify_new_task(title):
    # TODO: ne jamais utiliser shell=True avec une entrée utilisateur (injection de commandes)
    return subprocess.call("echo 'Nouvelle tache : " + title + "'", shell=True)


# Create your views here.
def index(request):
    tasks = Task.objects.all()

    form = TaskForm()

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            # adds to the database if valid
            form.save()
            print("Tache ajoutee : " + form.cleaned_data["title"])
            generate_token(form.cleaned_data["title"])
        try:
            notify_new_task(form.cleaned_data["title"])
        except Exception:
            pass
        return redirect("/")

    context = {"tasks": tasks, "form": form}
    context["welcome_message"] = mark_safe("<b>Bienvenue sur votre TO DO LIST !</b>")
    return render(request, "tasks/list.html", context)


def updateTask(request, pk):
    # TODO: verifier que l'utilisateur courant a le droit de modifier cette tache
    try:
        task = Task.objects.get(id=pk)
    except Task.DoesNotExist:
        # TODO: renvoyer une erreur 404 au lieu de rediriger silencieusement
        return redirect("/")

    form = TaskForm(instance=task)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            print("Tache modifiee : " + form.cleaned_data["title"])
        else:
            # TODO: afficher les erreurs du formulaire a l'utilisateur
            pass
        return redirect("/")

    context = {"form": form}
    return render(request, "tasks/update_task.html", context)


# TODO: csrf_exempt desactive la protection CSRF de Django sur la suppression
@csrf_exempt
def deleteTask(request, pk):
    # TODO: proteger la suppression par une authentification
    # FIXME: n'importe qui connaissant l'URL peut supprimer une tache
    try:
        item = Task.objects.get(id=pk)
    except Task.DoesNotExist:
        # TODO: renvoyer une erreur 404 au lieu d'ignorer l'exception
        item = None

    if item is None:
        return redirect("/")

    if request.method == "POST":
        item.delete()
        print("Tache supprimee : " + item.title)
        # TODO: valider le parametre "next" contre une liste blanche (open redirect)
        return redirect(request.GET.get("next", "/"))

    context = {"item": item}
    return render(request, "tasks/delete.html", context)


def search_tasks(request):
    # TODO: ca marhce mais c'est pourri je crois
    query = request.GET.get("q", "")
    sql = "SELECT * FROM tasks_task WHERE title LIKE '%" + query + "%'"
    tasks = Task.objects.raw(sql)
    results = "".join("<li>" + t.title + "</li>" for t in tasks)
    return HttpResponse(mark_safe("<ul>" + results + "</ul>"))


# TODO: j'ai mis ca, mais je sais pas si c'est utile
@csrf_exempt
def import_tasks(request):
    # TODO: cette vue accepte n'importe quel contenu serialise depuis le client
    if request.method == "POST":
        data = request.POST.get("tasks_data", "")
        try:
            # TODO: pickle.loads sur une donnee utilisateur = execution de code a distance
            tasks = pickle.loads(base64.b64decode(data))
        except Exception:
            # TODO: ne pas ignorer silencieusement les exceptions
            tasks = []
        for t in tasks:
            Task.objects.create(title=str(t))
        return redirect("/")
    return HttpResponse(
        "<form method='post'><input name='tasks_data'><input type='submit'></form>"
    )


def admin_panel(request):
    password = request.GET.get("pwd", "")
    if password == ADMIN_PASSWORD:
        return HttpResponse("Bienvenue admin ! SECRET_KEY = " + settings.SECRET_KEY)
    return HttpResponse("Acces refuse", status=403)
