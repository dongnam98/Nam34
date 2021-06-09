# coding: utf8

"""
This software is licensed under the Apache 2 license, quoted below.

Copyright 2014 Crystalnix Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
"""

import os

from django import test
from django.core.files.uploadedfile import SimpleUploadedFile

from mock import patch, call

from feedback.models import Feedback
from feedback.tasks import send_email_feedback

BASE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(BASE_DIR, 'testdata')
SYM_FILE = os.path.join(TEST_DATA_DIR, 'BreakpadTestApp.sym')
CRASH_DUMP_FILE = os.path.join(TEST_DATA_DIR, '7b05e196-7e23-416b-bd13-99287924e214.dmp')
INCORRECT_CRASH_DUMP_FILE = os.path.join(TEST_DATA_DIR, 'incorrect_minidump.dmp')
SYMBOLS_PATH = os.path.join(TEST_DATA_DIR, 'symbols')
STACKTRACE_PATH = os.path.join(TEST_DATA_DIR, 'stacktrace.txt')


class FeedbackTaskTest(test.TestCase):
    @patch('feedback.tasks.EmailMessage')
    def test_send_email(self, mock_email):
        mock_email_obj = mock_email.return_value
        description = 'Test description'
        email = 'me@example.com'
        page_url = 'http://google.com/'
        feedback_data = {
            'web_data': {
                'url': page_url
            },
            'common_data': {
                'description': description,
                'user_email': email,
          }
        }

        obj = Feedback.objects.create(
            description=description,
            email=email,
            page_url=page_url,
            screenshot=SimpleUploadedFile('./screenshot.png', b''),
            blackbox=SimpleUploadedFile('./blackbox.tar', b''),
            system_logs=SimpleUploadedFile('./sys_logs.zip', b''),
            attached_file=SimpleUploadedFile('./attach.zip', b''),
            feedback_data=feedback_data,
        )

        sender = 'sender@test.com'
        recipients = 'recepient1@test.com, recepient2@test.com'
        send_email_feedback(obj.pk, sender, recipients)

        # mock_email.assert_called_with('Feedback # %s' % obj.pk,
        #                               u"\nDescription: Test description\nPage URL: http://google.com/\nUser email: me@example.com\nUser IP: None\nFeedback JSON data: {u'web_data': {u'url': u'http://google.com/'}, u'common_data': {u'description': u'Test description', u'user_email': u'me@example.com'}}\n",
        #                               'sender@test.com', ['recepient1@test.com', 'recepient2@test.com'])
        mock_email.assert_called_once()
        mock_email_obj.send.assert_called_once()
        expected_attach_calls = [
            call('screenshot.png', b''),
            call('blackbox.tar', b''),
            call('sys_logs.zip', b''),
            call('attach.zip', b'')
        ]
        assert expected_attach_calls == mock_email_obj.attach.mock_calls
