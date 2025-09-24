# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt
"""

# stdlib
import os
from json import dumps
from logging import getLogger

# requests
import requests
from requests.exceptions import ConnectionError

# Zato
from zato.common.util.api import utcnow

# gevent
from gevent import sleep

# Zato
from zato.common.pubsub.perftest.python_.client import Client

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import anydict, intnone
    from zato.common.pubsub.perftest.python_.progress_tracker import ProgressTracker

# ################################################################################################################################
# ################################################################################################################################

logger = getLogger(__name__)

data2 = {'text': 'Integer urna. Vivamus molestie dapibus ligula. Aliquam erat volutpat. Nulla'}

data = [{
        'name': 'Eaton Freeman',
        'phone': '1-487-522-2778',
        'time': '3:24 AM',
        'company': 'Pharetra Felis Associates',
        'postalZip': '34026',
        'text': 'Integer urna. Vivamus molestie dapibus ligula. Aliquam erat volutpat. Nulla',
        'region': 'Jönköpings län',
        'guid': 'D263B5DF-E485-16B9-3E8E-9345F94C94C7',
        'iban': 'DE71816804964943650924154086',
        'track1': '%B3567251407726275^KqvzurfGzfygj^9209594857?5'
    },
    {
        'name': 'Brenda Wilkins',
        'phone': '(278) 654-2212',
        'time': '3:59 PM',
        'company': 'Rutrum Company',
        'postalZip': '031570',
        'text': 'ac orci. Ut semper pretium neque. Morbi quis urna. Nunc',
        'region': 'Zamboanga Peninsula',
        'guid': 'C35141C4-37C6-D1EA-ABDE-82EE2716041C',
        'iban': 'GB302638468295516128646303452',
        'track1': '%B3266028884335821^HfzilwlAfysdt^37072659?7'
    },
    {
        'name': 'Piper Chaney',
        'phone': '1-883-524-7463',
        'time': '11:12 PM',
        'company': 'Adipiscing Elit LLP',
        'postalZip': '25425',
        'text': 'pede et risus. Quisque libero lacus, varius et, euismod et,',
        'region': 'Stirlingshire',
        'guid': '666E2996-85AD-D2BE-D8BA-DA6C13CF6C0E',
        'iban': 'DE98VBVE73195715634752',
        'track1': '%B3365717117062201^DzbulyrNkacat^84051297?1'
    },
    {
        'name': 'Jacob Mercer',
        'phone': '(513) 457-4033',
        'time': '2:39 PM',
        'company': 'Non Foundation',
        'postalZip': '513321',
        'text': 'ligula. Aenean euismod mauris eu elit. Nulla facilisi. Sed neque.',
        'region': 'Luik',
        'guid': '69EC6286-7966-6B10-B8A0-E3A6C5731976',
        'iban': 'FR48569576145488431698712133',
        'track1': '%B8776285540045303^LdpmfrrBjflod^24119384?4'
    },
    {
        'name': 'Austin Bryan',
        'phone': '1-666-234-3029',
        'time': '8:28 PM',
        'company': 'Augue Sed Molestie LLP',
        'postalZip': '72431',
        'text': 'ligula tortor, dictum eu, placerat eget, venenatis a, magna. Lorem',
        'region': 'Yucatán',
        'guid': 'E5B55E39-62E6-8836-3652-E48482C6143E',
        'iban': 'FR98244805215102663149383298',
        'track1': '%B6867663289135515^KumxkcyLmeghj^64085553?4'
    },
    {
        'name': 'Eaton Freeman',
        'phone': '1-487-522-2778',
        'time': '3:24 AM',
        'company': 'Pharetra Felis Associates',
        'postalZip': '34026',
        'text': 'Integer urna. Vivamus molestie dapibus ligula. Aliquam erat volutpat. Nulla',
        'region': 'Jönköpings län',
        'guid': 'D263B5DF-E485-16B9-3E8E-9345F94C94C7',
        'iban': 'DE71816804964943650924154086',
        'track1': '%B3567251407726275^KqvzurfGzfygj^9209594857?5'
    },
    {
        'name': 'Brenda Wilkins',
        'phone': '(278) 654-2212',
        'time': '3:59 PM',
        'company': 'Rutrum Company',
        'postalZip': '031570',
        'text': 'ac orci. Ut semper pretium neque. Morbi quis urna. Nunc',
        'region': 'Zamboanga Peninsula',
        'guid': 'C35141C4-37C6-D1EA-ABDE-82EE2716041C',
        'iban': 'GB302638468295516128646303452',
        'track1': '%B3266028884335821^HfzilwlAfysdt^37072659?7'
    },
    {
        'name': 'Piper Chaney',
        'phone': '1-883-524-7463',
        'time': '11:12 PM',
        'company': 'Adipiscing Elit LLP',
        'postalZip': '25425',
        'text': 'pede et risus. Quisque libero lacus, varius et, euismod et,',
        'region': 'Stirlingshire',
        'guid': '666E2996-85AD-D2BE-D8BA-DA6C13CF6C0E',
        'iban': 'DE98VBVE73195715634752',
        'track1': '%B3365717117062201^DzbulyrNkacat^84051297?1'
    },
    {
        'name': 'Jacob Mercer',
        'phone': '(513) 457-4033',
        'time': '2:39 PM',
        'company': 'Non Foundation',
        'postalZip': '513321',
        'text': 'ligula. Aenean euismod mauris eu elit. Nulla facilisi. Sed neque.',
        'region': 'Luik',
        'guid': '69EC6286-7966-6B10-B8A0-E3A6C5731976',
        'iban': 'FR48569576145488431698712133',
        'track1': '%B8776285540045303^LdpmfrrBjflod^24119384?4'
    },
    {
        'name': 'Austin Bryan',
        'phone': '1-666-234-3029',
        'time': '8:28 PM',
        'company': 'Augue Sed Molestie LLP',
        'postalZip': '72431',
        'text': 'ligula tortor, dictum eu, placerat eget, venenatis a, magna. Lorem',
        'region': 'Yucatán',
        'guid': 'E5B55E39-62E6-8836-3652-E48482C6143E',
        'iban': 'FR98244805215102663149383298',
        'track1': '%B6867663289135515^KumxkcyLmeghj^64085553?4'
    },
    {
        'name': 'Brenda Wilkins',
        'phone': '(278) 654-2212',
        'time': '3:59 PM',
        'company': 'Rutrum Company',
        'postalZip': '031570',
        'text': 'ac orci. Ut semper pretium neque. Morbi quis urna. Nunc',
        'region': 'Zamboanga Peninsula',
        'guid': 'C35141C4-37C6-D1EA-ABDE-82EE2716041C',
        'iban': 'GB302638468295516128646303452',
        'track1': '%B3266028884335821^HfzilwlAfysdt^37072659?7'
    },
    {
        'name': 'Piper Chaney',
        'phone': '1-883-524-7463',
        'time': '11:12 PM',
        'company': 'Adipiscing Elit LLP',
        'postalZip': '25425',
        'text': 'pede et risus. Quisque libero lacus, varius et, euismod et,',
        'region': 'Stirlingshire',
        'guid': '666E2996-85AD-D2BE-D8BA-DA6C13CF6C0E',
        'iban': 'DE98VBVE73195715634752',
        'track1': '%B3365717117062201^DzbulyrNkacat^84051297?1'
    },
    {
        'name': 'Jacob Mercer',
        'phone': '(513) 457-4033',
        'time': '2:39 PM',
        'company': 'Non Foundation',
        'postalZip': '513321',
        'text': 'ligula. Aenean euismod mauris eu elit. Nulla facilisi. Sed neque.',
        'region': 'Luik',
        'guid': '69EC6286-7966-6B10-B8A0-E3A6C5731976',
        'iban': 'FR48569576145488431698712133',
        'track1': '%B8776285540045303^LdpmfrrBjflod^24119384?4'
    }
]

# ################################################################################################################################
# ################################################################################################################################

class Producer(Client):
    """ Producer client for publishing messages.
    """
    def __init__(self,
        progress_tracker:'ProgressTracker',
        reqs_per_producer:'int'=1,
        producer_id:'int'=0,
        reqs_per_second:'float'=1.0,
        topic_spec:'str'='3',
        burst_multiplier:'int'=10,
        burst_duration:'int'=10,
        burst_interval:'int'=60,
        cpu_num:'intnone'=None,
        use_new_requests:'bool'=False
    ) -> 'None':

        super().__init__(progress_tracker, producer_id, reqs_per_second, 3, cpu_num, use_new_requests)
        self.reqs_per_producer = reqs_per_producer
        self.topic_spec = topic_spec
        self.burst_multiplier = burst_multiplier
        self.burst_duration = burst_duration
        self.burst_interval = burst_interval

    def _get_config(self) -> 'anydict':
        """ Get configuration from environment variables.
        """
        base_url = os.environ['Zato_Test_PubSub_OpenAPI_URL_Producer']
        username = os.environ['Zato_Test_PubSub_OpenAPI_Username']
        password = os.environ['Zato_Test_PubSub_OpenAPI_Password']
        reqs_per_second = self.reqs_per_second
        max_topics = self.max_topics

        return {
            'base_url': base_url,
            'username': username,
            'password': password,
            'max_topics': max_topics,
            'reqs_per_second': reqs_per_second,
            'reqs_per_producer': self.reqs_per_producer,
            'topic_spec': self.topic_spec,
            'burst_multiplier': self.burst_multiplier,
            'burst_duration': self.burst_duration,
            'burst_interval': self.burst_interval,
        }

# ################################################################################################################################

    def _create_payload(self, topic_name:'str') -> 'anydict':
        """ Create message payload for publishing.
        """
        return {
            'data': {
                'message': {'msg':data},
                'topic': topic_name,
            },
            'priority': 5,
            'expiration': 3600 * 1000,
        }

# ################################################################################################################################

    def _publish_message(self, url:'str', payload:'anydict', headers:'anydict', auth:'tuple') -> 'None':
        """ Publish a single message to the broker.
        """
        try:
            response = self.session.post(url, data=dumps(payload), headers=headers, auth=auth)
            topic_name = payload['data']['topic']
            success = response.status_code == 200

            self.progress_tracker.update_progress(success)

            if not success:
                logger.error(f'Client {self.client_id}: Failed to publish to {topic_name}: {response.status_code} - {response.text}')
        except ConnectionError as e:
            topic_name = payload['data']['topic']
            logger.error(f'Client {self.client_id}: Failed to publish to {topic_name}: {e}')
            self.progress_tracker.update_progress(False)

# ################################################################################################################################

    def start(self) -> 'None':
        """ Start the producer.
        """
        cpu_info = f' (CPU: {self.cpu_num})' if self.cpu_num is not None else ''
        logger.info(f'Client {self.client_id}: Producer starting{cpu_info}')
        config = self._get_config()
        auth = (config['username'], config['password'])
        headers = {'Content-Type': 'application/json'}

        reqs_per_producer = config['reqs_per_producer']
        reqs_per_second = config['reqs_per_second']
        topic_spec = config['topic_spec']
        burst_multiplier = config['burst_multiplier']
        burst_duration = config['burst_duration']
        burst_interval = config['burst_interval']

        # Parse topic range
        if '-' in topic_spec:
            start_topic_str, end_topic_str = topic_spec.split('-', 1)
            start_topic = int(start_topic_str)
            end_topic = int(end_topic_str)
        else:
            topic_count = int(topic_spec)
            start_topic = 1
            end_topic = topic_count

        normal_interval = 1.0 / reqs_per_second
        if burst_multiplier > 0:
            burst_interval_time = 1.0 / (reqs_per_second * burst_multiplier)
        else:
            burst_interval_time = normal_interval

        start_time = utcnow()
        last_burst_time = start_time
        message_count = 0

        for _ in range(reqs_per_producer):
            for topic_num in range(start_topic, end_topic + 1):
                message_count += 1
                current_time = utcnow()

                # Check if we should start a burst (only if burst mode is enabled)
                is_in_burst = False
                if burst_interval > 0 and burst_duration > 0:
                    time_since_last_burst = (current_time - last_burst_time).total_seconds()
                    time_since_start = (current_time - start_time).total_seconds()

                    is_burst_time = time_since_last_burst >= burst_interval
                    is_in_burst = is_burst_time and (time_since_start % burst_interval) < burst_duration

                    if is_burst_time and not is_in_burst:
                        last_burst_time = current_time
                        is_in_burst = True

                request_start = utcnow()

                topic_name = f'demo.{topic_num}'
                url = f'{config["base_url"]}/pubsub/topic/{topic_name}'
                payload = self._create_payload(topic_name)

                self._publish_message(url, payload, headers, auth)

                request_end = utcnow()
                request_duration = (request_end - request_start).total_seconds()

                # Use appropriate interval based on burst mode
                target_interval = burst_interval_time if is_in_burst else normal_interval
                sleep_time = target_interval - request_duration

                if sleep_time > 0:
                    sleep(sleep_time)

# ################################################################################################################################
# ################################################################################################################################
