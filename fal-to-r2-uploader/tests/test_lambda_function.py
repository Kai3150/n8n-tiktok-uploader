import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dependencies'))

import json
import pytest
from unittest.mock import patch, MagicMock
from lambda_function import lambda_handler, get_r2_credentials


class TestFalToR2Uploader:

    @patch('lambda_function.get_r2_credentials')
    @patch('lambda_function.boto3.client')
    @patch('lambda_function.requests.get')
    def test_lambda_handler_success(self, mock_requests_get, mock_boto3_client, mock_get_r2_credentials):
        mock_get_r2_credentials.return_value = {
            'endpoint_url': 'https://test-endpoint.com',
            'access_key_id': 'test-key',
            'secret_access_key': 'test-secret'
        }

        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.raw = MagicMock()
        mock_requests_get.return_value = mock_response

        event = {
            'body': json.dumps({
                'video_url': 'https://v3.fal.media/files/test/video.mp4'
            })
        }

        result = lambda_handler(event, {})

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['success'] is True
        assert 'r2_url' in response_body
        assert 'filename' in response_body

        mock_s3_client.upload_fileobj.assert_called_once()

    def test_lambda_handler_missing_video_url(self):
        event = {
            'body': json.dumps({})
        }

        result = lambda_handler(event, {})

        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert response_body['success'] is False
        assert 'video_url is required' in response_body['error']

    @patch('lambda_function.boto3.client')
    def test_get_r2_credentials_success(self, mock_boto3_client):
        mock_secrets_client = MagicMock()
        mock_boto3_client.return_value = mock_secrets_client

        mock_secrets_client.get_secret_value.side_effect = [
            {'SecretString': 'https://test-endpoint.com'},
            {'SecretString': 'test-key'},
            {'SecretString': 'test-secret'}
        ]

        credentials = get_r2_credentials()

        assert credentials['endpoint_url'] == 'https://test-endpoint.com'
        assert credentials['access_key_id'] == 'test-key'
        assert credentials['secret_access_key'] == 'test-secret'


if __name__ == '__main__':
    pytest.main([__file__])
