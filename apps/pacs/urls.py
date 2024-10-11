from django.urls import include, path

#from .views import CustomerList, EventList
from . import views

urlpatterns = [
    #path('', EventList.as_view()),
    path('', views.get_all_events)
]