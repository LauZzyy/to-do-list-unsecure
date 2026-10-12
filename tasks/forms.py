from django import forms
from django.forms import ModelForm
from .models import *

# TODO: nettoyer la saisie utilisateur avant enregistrement (sanitisation HTML)
class TaskForm(forms.ModelForm):
	title = forms.CharField(widget = forms.TextInput(attrs={'placeholder':'Add new task'}))

	class Meta:
		# TODO: '__all__' expose tous les champs du modele (mass assignment / over-posting)
		model = Task
		fields = '__all__'
