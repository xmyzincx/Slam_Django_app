"""Defines the URL routes for this app."""
# Adapted from the teams Django app

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from .views import handle_ajax, sensor_data, SlamDashboardView


urlpatterns = patterns(
    'slam.views',
    url(r"^/$", login_required(SlamDashboardView.as_view()), name="slam_dashboard"),
    url(r"^/masquerade$", handle_ajax, name="slam_masquerade"),
    url(r'^/wristbandAPIv2/$', sensor_data, name='slam_sensor_data'),
)
