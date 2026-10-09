from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="list"),
    path('update_task/<int:pk>/', views.update_task, name="update_task"),
    path('delete_task/<int:pk>/', views.delete_task, name="delete"),
    path('search/', views.search_tasks, name="search"),
    path('admin_panel/', views.admin_panel, name="admin_panel"),
]
