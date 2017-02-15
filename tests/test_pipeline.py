from __future__ import unicode_literals, print_function
import os
import shutil
import tempfile
import uuid
from unittest import TestCase
from general_tools.file_utils import unzip, read_file
from mock import patch
from webhook import main as webhook
from general_tools.file_utils import load_json_object


class TestPipeline(TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    class JsonObject(object):
        def __init__(self, value_dict):
            self.__dict__ = value_dict

    @staticmethod
    def mock_download_repo(source, target_dir):
        print('Mock downloading {}'.format(source))
        print('Unzipping to {}...'.format(target_dir), end=' ')
        unzip(os.path.join(TestPipeline.resources_dir, 'en-obs-master.zip'), target_dir)
        print('finished.')

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_s3_upload_file(source, key, cache_time=600):
        print('Mock uploading {}'.format(source))

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_s3_get_objects(prefix=None, suffix=None):
        print('Mock get objects')

        if prefix == 'u/Door43/en-obs/e323f37de1':
            return []

    # noinspection PyUnusedLocal
    @staticmethod
    def mock_requests_post(url, json=None, headers=None):
        print('Mock posting {}'.format(url))

        if url == 'unit_test_api_url/tx/job':
            response = {
                'status_code': 200,
                'text': read_file(os.path.join(TestPipeline.resources_dir, 'en-obs-job-resp.json'))
            }
            return TestPipeline.JsonObject(response)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='unitTest_')

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('requests.post')
    @patch('webhook.main.download_repo')
    @patch('webhook.main.S3Handler.get_objects')
    @patch('webhook.main.S3Handler.upload_file')
    def test_obs_ts_pipeline(self, mock_s3_upload, mock_s3_get_objects, mock_download_repo, mock_post):
        """

        :param MagicMock mock_s3_upload:
        :param MagicMock mock_s3_get_objects:
        :param MagicMock mock_download_repo:
        :param MagicMock mock_post:
        :return:
        """

        mock_download_repo.side_effect = self.mock_download_repo
        mock_s3_upload.side_effect = self.mock_s3_upload_file
        mock_s3_get_objects.side_effect = self.mock_s3_get_objects
        mock_post.side_effect = self.mock_requests_post

        # create test event variable
        event = {'vars': load_json_object(os.path.join(self.resources_dir, 'en-obs-vars.json')),
                 'data': load_json_object(os.path.join(self.resources_dir, 'en-obs-payload.json'))}

        # create test context variable
        context = TestPipeline.JsonObject({'aws_request_id': str(uuid.uuid4())[-10:]})

        # fire the web hook
        webhook.handle(event, context)

        # check that the mocks are working
        self.assertIn('https://git.door43.org/Door43/en-obs/commit/e323f37de1ad2c063a3659c58494edbb2641ce54',
                      mock_download_repo.call_args[0])

    def test_obs_rc_pipeline(self):

        self.skipTest('Not implemented yet')

        self.assertTrue(False, 'Not implemented')
