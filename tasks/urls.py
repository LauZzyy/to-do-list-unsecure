from django.urls import path
from . import views
urlpatterns = [
	path('', views.index, name="list"),
	path('update_task/<str:pk>/', views.updateTask, name="update_task"),
	path('delete_task/<str:pk>/', views.deleteTask, name="delete"),
	# TODO: ces routes expose des fonctionnalites volontairement non securisees
	path('search/', views.search_tasks, name="search"),
	path('import/', views.import_tasks, name="import_tasks"),
	path('admin_panel/', views.admin_panel, name="admin_panel"),

	
]