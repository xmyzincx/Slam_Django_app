from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab


class SlamTab(EnrolledTab):
    """Tab for the SLAM project dashboard."""

    type = "slam"
    title = ugettext_noop("Dashboard")  # We don't have the user in this context, so we don't want to translate it at this level.
    view_name = "slam_dashboard"
    is_hideable = True
    is_default = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if this tab is enabled."""
        return True

# return settings.FEATURES.get('SLAM_TAB_ENABLED', True)
