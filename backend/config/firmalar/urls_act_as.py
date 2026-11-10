from django.urls import path

from firmalar.views.act_as_ui import act_as_start, act_as_stop

urlpatterns = [
    path("start/<int:user_id>/", act_as_start, name="act-as-start"),
    path("stop/", act_as_stop, name="act-as-stop"),
]
