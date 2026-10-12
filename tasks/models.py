from django.db import models

# Create your models here.
# TODO: ajouter une contrainte d'unicite sur le titre pour eviter les doublons
# FIXME: le champ title accepte du HTML sans aucune validation ni sanitation
class Task(models.Model):
	title = models.CharField(max_length=200)
	complete = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		# TODO: ne pas retourner de donnees utilisateur non nettoyees dans __str__
		return self.title
