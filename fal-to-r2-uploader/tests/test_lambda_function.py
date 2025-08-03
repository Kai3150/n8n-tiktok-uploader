import sys
import os
# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from unittest.mock import patch, MagicMock
from lambda_function import lambda_handler


class TestFalToR2Uploader:

    @patch('lambda_function.boto3.client')
    @patch('lambda_function.requests.get')
    def test_lambda_handler_success(self, mock_requests_get, mock_boto3_client):

        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.content = b'fake_video_content'
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        event = {
            'body': json.dumps({
                'video_url': 'https://v3.fal.media/files/rabbit/PWegvgzZwbX2TYt3pNtwr_output.mp4'
            })
        }

        result = lambda_handler(event, {})
        print(result)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['success'] is True
        assert 'r2_url' in response_body
        assert 'filename' in response_body


    def test_lambda_handler_missing_video_url(self):
        event = {
            'body': json.dumps({})
        }

        result = lambda_handler(event, {})

        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert response_body['success'] is False
        assert 'video_url is required' in response_body['error']


if __name__ == '__main__':
    pytest.main([__file__])
