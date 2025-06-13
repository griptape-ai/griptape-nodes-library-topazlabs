"""HTTP client for Topaz Labs API."""

import sys
import os
import requests
from typing import Dict, Any, Union, BinaryIO

# Add current directory to path for constants import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from constants import API_BASE_URL


class TopazClient:
    """Client for interacting with Topaz Labs API."""
    
    def __init__(self, api_key: str):
        """Initialize the client with API key.
        
        Args:
            api_key: The Topaz Labs API key
        """
        self.api_key = api_key
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'accept': 'image/jpeg'
        })
    
    def denoise(self, image_data: Union[bytes, BinaryIO], **params) -> bytes:
        """Call the denoise endpoint.
        
        Args:
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the denoise API
            
        Returns:
            Binary image data
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        return self._make_request("denoise", image_data, **params)
    
    def enhance(self, image_data: Union[bytes, BinaryIO], **params) -> bytes:
        """Call the enhance endpoint for standard (GAN) models.
        
        Args:
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the enhance API
            
        Returns:
            Binary image data
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        return self._make_request("enhance", image_data, **params)
    
    def enhance_gen(self, image_data: Union[bytes, BinaryIO], **params) -> bytes:
        """Call the enhance-gen endpoint for generative models.
        
        Args:
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the generative enhance API
            
        Returns:
            Binary image data
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        return self._make_request("enhance-gen", image_data, **params)
    
    def _make_request(self, endpoint: str, image_data: Union[bytes, BinaryIO], **params) -> bytes:
        """Make a request to the Topaz Labs API.
        
        Args:
            endpoint: API endpoint (denoise, enhance, enhance-gen, etc.)
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the API
            
        Returns:
            Binary image data
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Prepare files dict for multipart upload
        files = {'image': ('image.jpg', image_data, 'image/jpeg')}
        
        # Filter out None values and prepare form data
        form_data = {k: str(v) for k, v in params.items() if v is not None}
        
        try:
            response = self.session.post(
                url,
                files=files,
                data=form_data,
                timeout=300  # 5 minute timeout for processing
            )
            response.raise_for_status()
            
            # Validate response content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"Unexpected content type: {content_type}")
            
            return response.content
            
        except requests.exceptions.Timeout:
            raise requests.HTTPError("Request timed out. Image processing may take longer than expected.")
        except requests.exceptions.ConnectionError:
            raise requests.HTTPError("Connection error. Please check your internet connection.")
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise
        except Exception as e:
            raise requests.HTTPError(f"Unexpected error: {str(e)}")
    
    def _handle_http_error(self, response: requests.Response, error: requests.HTTPError) -> None:
        """Handle HTTP errors with meaningful messages.
        
        Args:
            response: The HTTP response object
            error: The original HTTP error
        """
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_message = error_data.get('message', 'Unknown error')
        except:
            error_message = response.text or 'Unknown error'
        
        if status_code == 401:
            raise requests.HTTPError(f"Authentication failed. Please check your API key. ({error_message})")
        elif status_code == 429:
            raise requests.HTTPError(f"Rate limit exceeded. Please wait and try again. ({error_message})")
        elif status_code >= 500:
            raise requests.HTTPError(f"Server error. Please try again later. ({error_message})")
        else:
            raise requests.HTTPError(f"API error ({status_code}): {error_message}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close() 