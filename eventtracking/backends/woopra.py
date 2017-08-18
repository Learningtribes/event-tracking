"""Event tracking backend that sends events to woopra.com"""

from __future__ import absolute_import

from track.backends import BaseBackend
from woopra import WoopraTracker

import logging

LOG = logging.getLogger(__name__)

class WoopraBackend(BaseBackend):
    """
    Event tracker backend that send events to woopra.com

    :Parameters:

    - `url`: URL registered for the project in Woopra
    - `idle_timeout`: the timeout in milliseconds after which the event will expire
        and the visit will be marked as offline
    - `secure`: configure the secure (https) tracking

    """

    IDLE_TIMEOUT = 300000
    IS_SECURE = True

    SETTINGS_CHANGED_EVENT = "edx.user.settings.changed"
    PROBLEM_CHECK_EVENT = "problem_check"
    PROGRESS_EVENT = "lt.progress_summary"
    COURSEWARE_EVENT = "courseware"

    def __init__(self, **kwargs):
        super(WoopraBackend, self).__init__(**kwargs)
        self.url = kwargs.get('url', None)
        self.idle_timeout = kwargs.get('idle_timeout', self.IDLE_TIMEOUT)
        self.is_secure = kwargs.get('secure', self.IS_SECURE)


    def send(self, event):
        """Use the woopra.com python API to send the event to woopra.com"""
        if self.url:
            LOG.critical('EVENT-TRACKING WoopraBackend: WANT TO SEND to %s', self.url)

            event_name = event.get('name', '')
            event_type = event.get('event_type', '')
            if len(event_name) == 0:
                event_name = event_type
            LOG.critical('EVENT-TRACKING WoopraBackend: TRY TO SEND %s', event_name)

            username = event.get('username', '')
            LOG.critical('EVENT-TRACKING WoopraBackend: TRY TO SEND for user %s', username)

            if len(username) == 0 or len(event_name) == 0:
                LOG.critical('EVENT-TRACKING WoopraBackend: DO NOT SEND %s', event_name)
                return

            try:
                woopra = WoopraTracker(self.url)
                woopra.set_secure(self.is_secure)
                woopra.set_idle_timeout(self.idle_timeout)

                user_properties = {
                    'id': username,
                    'username': username,
                }
                user_id = event.get('context', {}).get('user_id')
                if user_id is not None:
                    user_properties['user_id'] = user_id

                if event_name == self.SETTINGS_CHANGED_EVENT:
                    prop = event.get('event').get('setting')
                    prop_new_val = event.get('event').get('new')
                    user_properties[prop] = prop_new_val

                event_user_properties = event.get('user_properties')
                if event_user_properties is not None and event_name == self.PROGRESS_EVENT:
                    for prop, val in event_user_properties.iteritems():
                        user_properties[prop] = val

                if event_name.find(self.COURSEWARE_EVENT) >=0:
                    course_id = event.get('context', {}).get('course_id')
                    if course_id is not None:
                        # from course_id like 'course-v1:GOS+GOS101+2017_T2'
                        # to property like 'gos101_2017_t2_started'
                        course_id = course_id.lower()
                        index = course_id.find('+') + 1
                        course_id = course_id[index:].replace('+', '_')
                        course_started_prop = "%s_started"% course_id
                        user_properties[course_started_prop] = 1

                woopra.identify(user_properties)

                if event_name == self.PROBLEM_CHECK_EVENT:
                   if event_type == self.PROBLEM_CHECK_EVENT and event.get('event_source', '') == "server":
                       event_name = "lt.%s" % self.PROBLEM_CHECK_EVENT
                       woopra.track(event_name, event)
                       LOG.critical('EVENT-TRACKING WoopraBackend: SENT %s', event_name)
                   else:
                       LOG.critical('EVENT-TRACKING WoopraBackend: DID NOT SEND %s', event_name)
                else:
                    woopra.track(event_name, event)
                    LOG.critical('EVENT-TRACKING WoopraBackend: SENT %s', event_name)

            except:
                LOG.error('EVENT-TRACKING WoopraBackend: EXCEPTION')
                raise

