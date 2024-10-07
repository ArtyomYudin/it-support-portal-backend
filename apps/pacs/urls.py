from django.urls import include, path
from .views import CustomerList, EventList


urlpatterns = [
    path('', EventList.as_view()),
]