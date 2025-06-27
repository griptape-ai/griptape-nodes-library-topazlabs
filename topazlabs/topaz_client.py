"""HTTP client for Topaz Labs API."""

import sys
import os
import requests
import time
import json
from typing import Dict, Any, Union, BinaryIO, Optional

# Add current directory to path for constants import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from constants import API_BASE_URL, VIDEO_API_BASE_URL


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
            'X-API-Key': api_key
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
    
    def enhance_gen(self, image_data: Union[bytes, BinaryIO], poll_interval: int = 5, max_wait_time: int = 300, **params) -> bytes:
        """
        Orchestrates an asynchronous call to the enhance-gen endpoint.
        This involves starting the job, polling for completion, and downloading the result.
        
        Args:
            image_data: Image data as bytes or file-like object.
            poll_interval: Seconds to wait between status checks.
            max_wait_time: Maximum seconds to wait for the job to complete.
            **params: Additional parameters for the generative enhance API.
            
        Returns:
            Binary image data of the processed image.
            
        Raises:
            TimeoutError: If the job doesn't complete within max_wait_time.
            requests.HTTPError: If any API request fails.
        """
        # Step 1: Start the async job
        start_response = self._make_request("enhance-gen/async", image_data, returns_json=True, **params)
        process_id = start_response.get("process_id")
        if not process_id:
            raise ValueError("API response did not include a process_id.")

        # Step 2: Poll for completion
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_response = self.get_status(process_id)
            status = status_response.get("status")

            if status == "Completed":
                # Step 3: Download the result
                return self.download_output(process_id)
            elif status == "Failed":
                raise requests.HTTPError(f"Image processing failed with status: {status}")
            
            time.sleep(poll_interval)

        raise TimeoutError(f"Image processing did not complete within {max_wait_time} seconds.")

    def get_status(self, process_id: str) -> Dict[str, Any]:
        """Get the status of a job."""
        url = f"{self.base_url}/status/{process_id}"
        try:
            headers = {'Accept': 'application/json'}
            response = self.session.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise

    def download_output(self, process_id: str) -> bytes:
        """Download the output of a completed job."""
        # Get the download URL
        url = f"{self.base_url}/download/{process_id}"
        try:
            headers = {'Accept': 'application/json'}
            response = self.session.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            download_info = response.json()
            download_url = download_info.get("download_url")

            if not download_url:
                raise ValueError("Download endpoint did not return a download_url.")

            # Download the actual image from the presigned URL
            download_response = requests.get(download_url, timeout=300)
            download_response.raise_for_status()
            return download_response.content
        
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise

    def _make_request(self, endpoint: str, image_data: Union[bytes, BinaryIO], returns_json: bool = False, **params) -> Union[bytes, Dict]:
        """Make a request to the Topaz Labs API.
        
        Args:
            endpoint: API endpoint (denoise, enhance, enhance-gen, etc.)
            image_data: Image data as bytes or file-like object
            returns_json: If True, parses and returns JSON response. Otherwise, returns content bytes.
            **params: Additional parameters for the API
            
        Returns:
            Binary image data or JSON response dictionary
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        print(f"DEBUG CLIENT: Received params: {params}")
        
        # Prepare files dict for multipart upload
        files = {'image': ('image.jpg', image_data, 'image/jpeg')}
        
        # Filter out None values and prepare form data
        form_data = {}
        for k, v in params.items():
            if v is not None:
                if isinstance(v, bool):
                    # Convert boolean to lowercase string for form data
                    converted_value = 'true' if v else 'false'
                    print(f"DEBUG: Converting boolean {k}={v} ({type(v)}) to '{converted_value}'")
                    form_data[k] = converted_value
                else:
                    form_data[k] = str(v)
        
        print(f"DEBUG: Final form_data being sent to API: {form_data}")
        
        headers = {}
        if returns_json:
            headers['Accept'] = 'application/json'
        else:
            # Default to jpeg, but allow override from params
            output_format = params.get("output_format", "jpeg")
            headers['Accept'] = f"image/{output_format}"

        try:
            response = self.session.post(
                url,
                files=files,
                data=form_data,
                headers=headers,
                timeout=300  # 5 minute timeout for processing
            )
            response.raise_for_status()
            
            if returns_json:
                return response.json()

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
    
    # Video API Methods
    def create_video_request(self, source_info: Dict[str, Any], output_config: Dict[str, Any], 
                           filters: list[Dict[str, Any]]) -> str:
        """Create a video processing request.
        
        Args:
            source_info: Source video information (resolution, container, size, etc.)
            output_config: Output configuration (resolution, codecs, etc.)
            filters: List of filter configurations
            
        Returns:
            Request ID for the video processing job
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/"
        
        request_data = {
            "source": source_info,
            "output": output_config,
            "filters": filters
        }
        
        try:
            response = self.session.post(
                url,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            request_id = result.get("requestId")
            
            if not request_id:
                raise ValueError(f"No requestId in response. Response: {result}")
            
            return request_id
            
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise
    
    def accept_video_request(self, request_id: str) -> Dict[str, Any]:
        """Accept a video processing request and get upload URL.
        
        Args:
            request_id: The video processing request ID
            
        Returns:
            Dictionary containing upload URL and other details
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/accept"
        
        try:
            response = self.session.patch(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise
    
    def upload_video(self, upload_url: str, video_data: bytes, content_type: str = "video/mp4") -> str:
        """Upload video data to the provided S3 URL.
        
        Args:
            upload_url: S3 upload URL from accept_video_request
            video_data: Video file data as bytes
            content_type: MIME type of the video file
            
        Returns:
            ETag from the S3 upload response
            
        Raises:
            requests.HTTPError: If the upload fails
        """
        response = requests.put(
            upload_url,
            data=video_data,
            headers={"Content-Type": content_type},
            timeout=600  # 10 minutes for upload
        )
        response.raise_for_status()
        
        # Extract ETag from response headers
        etag = response.headers.get("ETag", "").strip('"')
        if not etag:
            raise ValueError("No ETag received from S3 upload")
        
        return etag
    
    def complete_video_upload(self, request_id: str, etag: str) -> None:
        """Signal that video upload is complete.
        
        Args:
            request_id: The video processing request ID
            etag: ETag from the S3 upload response
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/complete-upload"
        
        payload = {
            "uploadResults": [
                {
                    "partNum": 1,
                    "eTag": etag
                }
            ]
        }
        
        try:
            response = self.session.patch(
                url, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, e)
            raise
    
    def get_video_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a video processing request.
        
        Args:
            request_id: The video processing request ID
            
        Returns:
            Status information including progress and download URL when complete
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/status"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def process_video_complete(self, video_data: bytes, source_info: Dict[str, Any], 
                             output_config: Dict[str, Any], filters: list[Dict[str, Any]], 
                             max_wait_time: int = 3600, poll_interval: int = 10, 
                             progress_callback=None) -> bytes:
        """Complete video processing workflow from upload to download.
        
        Args:
            video_data: Video file data as bytes
            source_info: Source video information
            output_config: Output configuration
            filters: List of filter configurations
            max_wait_time: Maximum time to wait for processing (seconds)
            poll_interval: How often to check status (seconds)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Processed video data as bytes
            
        Raises:
            requests.HTTPError: If any step fails
            TimeoutError: If processing takes longer than max_wait_time
        """
        # Step 1: Create request
        request_id = self.create_video_request(source_info, output_config, filters)
        
        # Step 2: Accept request and get upload URL
        accept_response = self.accept_video_request(request_id)
        
        # Extract upload URL from the response structure: {"uploadId": "...", "urls": [url1, url2, ...]}
        urls = accept_response.get("urls", [])
        upload_url = urls[0] if urls else None
        
        if not upload_url:
            raise ValueError(f"No upload URL in response. Response: {accept_response}")
        
        # Step 3: Upload video
        etag = self.upload_video(upload_url, video_data)
        
        # Step 4: Complete upload
        self.complete_video_upload(request_id, etag)
        
        # Step 5: Poll for completion
        start_time = time.time()
        poll_count = 0
        
        if progress_callback:
            progress_callback(40, "Processing video... (checking status)")
        
        while time.time() - start_time < max_wait_time:
            status = self.get_video_status(request_id)
            poll_count += 1
            
            # Calculate progress based on time elapsed (rough estimate)
            elapsed_time = time.time() - start_time
            estimated_progress = min(40 + int((elapsed_time / max_wait_time) * 50), 89)
            
            current_status = status.get("status", "unknown")
            progress_percent = status.get("progress", estimated_progress)
            
            if progress_callback:
                status_msg = status.get("message", f"Processing... (status: {current_status})")
                progress_callback(progress_percent, status_msg)
            
            if current_status == "complete":
                if progress_callback:
                    progress_callback(90, "Processing complete, downloading result...")
                
                download_info = status.get("download", {})
                download_url = download_info.get("url")
                
                if download_url:
                    # Download the processed video
                    download_response = requests.get(download_url, timeout=600)
                    download_response.raise_for_status()
                    return download_response.content
                else:
                    raise ValueError("No download URL in completion response")
            
            elif current_status == "failed":
                error_message = status.get("message", "Processing failed")
                raise requests.HTTPError(f"Video processing failed: {error_message}")
            
            # Wait before next poll
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Video processing did not complete within {max_wait_time} seconds") 