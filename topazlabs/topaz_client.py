"""HTTP client for Topaz Labs API."""

import os
import sys
import time
from collections.abc import Callable
from typing import Any, BinaryIO

import requests

# Add current directory to path for constants import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from constants import API_BASE_URL, VIDEO_API_BASE_URL
from topaz_errors import (
    connection_error,
    job_failed_error,
    job_timeout_error,
    raise_for_status,
    storage_error,
    timeout_error,
    unexpected_response_error,
)


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
        self.session.headers.update({"X-API-Key": api_key})

    def denoise(self, image_data: bytes | BinaryIO, **params) -> bytes:
        """Call the denoise endpoint.

        Args:
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the denoise API

        Returns:
            Binary image data

        Raises:
            NodeError: If the API request fails
        """
        return self._make_request("denoise", image_data, **params)

    def enhance(self, image_data: bytes | BinaryIO, **params) -> bytes:
        """Call the enhance endpoint for standard (GAN) models.

        Args:
            image_data: Image data as bytes or file-like object
            **params: Additional parameters for the enhance API

        Returns:
            Binary image data

        Raises:
            NodeError: If the API request fails
        """
        return self._make_request("enhance", image_data, **params)

    def enhance_gen(
        self, image_data: bytes | BinaryIO, poll_interval: int = 5, max_wait_time: int = 300, **params
    ) -> bytes:
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
            NodeError: If any API request fails or the job doesn't complete within max_wait_time.
        """
        # Step 1: Start the async job
        start_response = self._make_request("enhance-gen/async", image_data, returns_json=True, **params)
        if not isinstance(start_response, dict):
            raise unexpected_response_error("the response is not a JSON object")
        process_id = start_response.get("process_id")
        if not process_id:
            raise unexpected_response_error("the response has no process_id", start_response)

        # Step 2: Poll for completion
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_response = self.get_status(process_id)
            status = status_response.get("status")

            if status == "Completed":
                # Step 3: Download the result
                return self.download_output(process_id)
            elif status == "Failed":
                raise job_failed_error(status_response.get("message"), status_response, job_id=process_id)

            time.sleep(poll_interval)

        raise job_timeout_error(max_wait_time, job_id=process_id)

    def get_status(self, process_id: str) -> dict[str, Any]:
        """Get the status of a job."""
        url = f"{self.base_url}/status/{process_id}"
        headers = {"Accept": "application/json"}
        try:
            response = self.session.get(url, timeout=30, headers=headers)
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        raise_for_status(response, job_id=process_id)
        return response.json()

    def download_output(self, process_id: str) -> bytes:
        """Download the output of a completed job."""
        # Get the download URL
        url = f"{self.base_url}/download/{process_id}"
        headers = {"Accept": "application/json"}
        try:
            response = self.session.get(url, timeout=30, headers=headers)
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        raise_for_status(response, job_id=process_id)
        download_info = response.json()
        download_url = download_info.get("download_url")

        if not download_url:
            raise unexpected_response_error("the response has no download_url", download_info, job_id=process_id)

        return self.download_file(download_url, "Downloading the processed image", timeout=300, job_id=process_id)

    def download_file(
        self,
        url: str,
        action: str,
        *,
        timeout: int = 600,
        request_id: str | None = None,
        job_id: str | None = None,
    ) -> bytes:
        """Download a processed file from its presigned URL.

        Args:
            url: The presigned download URL
            action: What the node is doing, as a phrase such as "Downloading the processed video"
            timeout: Seconds to wait for the download
            request_id: The video request this file belongs to, when there is one
            job_id: The generative job this file belongs to, when there is one

        Raises:
            NodeError: If the download times out, cannot connect, or returns an error status.
        """
        try:
            response = requests.get(url, timeout=timeout)
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        if not response.ok:
            raise storage_error(response, action, request_id=request_id, job_id=job_id)
        return response.content

    def _make_request(
        self, endpoint: str, image_data: bytes | BinaryIO, returns_json: bool = False, **params
    ) -> bytes | dict:
        """Make a request to the Topaz Labs API.

        Args:
            endpoint: API endpoint (denoise, enhance, enhance-gen, etc.)
            image_data: Image data as bytes or file-like object
            returns_json: If True, parses and returns JSON response. Otherwise, returns content bytes.
            **params: Additional parameters for the API

        Returns:
            Binary image data or JSON response dictionary

        Raises:
            NodeError: If the API request fails
        """
        url = f"{self.base_url}/{endpoint}"

        print(f"DEBUG CLIENT: Received params: {params}")

        # Prepare files dict for multipart upload
        files = {"image": ("image.jpg", image_data, "image/jpeg")}

        # Filter out None values and prepare form data
        form_data = {}
        for k, v in params.items():
            if v is not None:
                if isinstance(v, bool):
                    # Convert boolean to lowercase string for form data
                    converted_value = "true" if v else "false"
                    print(f"DEBUG: Converting boolean {k}={v} ({type(v)}) to '{converted_value}'")
                    form_data[k] = converted_value
                else:
                    form_data[k] = str(v)

        print(f"DEBUG: Final form_data being sent to API: {form_data}")

        headers = {}
        if returns_json:
            headers["Accept"] = "application/json"
        else:
            # Default to jpeg, but allow override from params
            output_format = params.get("output_format", "jpeg")
            headers["Accept"] = f"image/{output_format}"

        try:
            response = self.session.post(
                url,
                files=files,
                data=form_data,
                headers=headers,
                timeout=300,  # 5 minute timeout for processing
            )
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        raise_for_status(response)

        if returns_json:
            return response.json()

        # Validate response content type
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise unexpected_response_error(f"expected an image but received '{content_type}'")

        return response.content

    def _send(self, call: Callable[[], requests.Response], *, request_id: str | None = None) -> requests.Response:
        """Run a Topaz Labs API call and raise a NodeError if it fails or returns an error status."""
        try:
            response = call()
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        raise_for_status(response, request_id=request_id)
        return response

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()

    # Video API Methods
    def create_video_request(
        self, source_info: dict[str, Any], output_config: dict[str, Any], filters: list[dict[str, Any]]
    ) -> str:
        """Create a video processing request.

        Args:
            source_info: Source video information (resolution, container, size, etc.)
            output_config: Output configuration (resolution, codecs, etc.)
            filters: List of filter configurations

        Returns:
            Request ID for the video processing job

        Raises:
            NodeError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/"

        request_data = {"source": source_info, "output": output_config, "filters": filters}

        response = self._send(
            lambda: self.session.post(url, json=request_data, headers={"Content-Type": "application/json"}, timeout=30)
        )

        result = response.json()
        request_id = result.get("requestId")

        if not request_id:
            raise unexpected_response_error("the response has no requestId", result)

        return request_id

    def accept_video_request(self, request_id: str) -> dict[str, Any]:
        """Accept a video processing request and get upload URL.

        Args:
            request_id: The video processing request ID

        Returns:
            Dictionary containing upload URL and other details

        Raises:
            NodeError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/accept"

        response = self._send(lambda: self.session.patch(url, timeout=30), request_id=request_id)
        return response.json()

    def upload_video(self, upload_url: str, video_data: bytes, content_type: str = "video/mp4") -> str:
        """Upload video data to the provided S3 URL.

        Args:
            upload_url: S3 upload URL from accept_video_request
            video_data: Video file data as bytes
            content_type: MIME type of the video file

        Returns:
            ETag from the S3 upload response

        Raises:
            NodeError: If the upload fails
        """
        try:
            response = requests.put(
                upload_url,
                data=video_data,
                headers={"Content-Type": content_type},
                timeout=600,  # 10 minutes for upload
            )
        except requests.exceptions.Timeout as e:
            raise timeout_error() from e
        except requests.exceptions.ConnectionError as e:
            raise connection_error() from e
        if not response.ok:
            raise storage_error(response, "Uploading the video")

        # Extract ETag from response headers
        etag = response.headers.get("ETag", "").strip('"')
        if not etag:
            raise unexpected_response_error("the video upload returned no ETag")

        return etag

    def complete_video_upload(self, request_id: str, etag: str) -> None:
        """Signal that video upload is complete.

        Args:
            request_id: The video processing request ID
            etag: ETag from the S3 upload response

        Raises:
            NodeError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/complete-upload"

        payload = {"uploadResults": [{"partNum": 1, "eTag": etag}]}

        self._send(
            lambda: self.session.patch(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30),
            request_id=request_id,
        )

    def get_video_status(self, request_id: str) -> dict[str, Any]:
        """Get the status of a video processing request.

        Args:
            request_id: The video processing request ID

        Returns:
            Status information including progress and download URL when complete

        Raises:
            NodeError: If the API request fails
        """
        url = f"{VIDEO_API_BASE_URL}/{request_id}/status"

        response = self._send(lambda: self.session.get(url, timeout=30), request_id=request_id)
        return response.json()

    def process_video_complete(
        self,
        video_data: bytes,
        source_info: dict[str, Any],
        output_config: dict[str, Any],
        filters: list[dict[str, Any]],
        max_wait_time: int = 3600,
        poll_interval: int = 10,
        progress_callback=None,
    ) -> bytes:
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
            NodeError: If any step fails
            NodeError: If processing takes longer than max_wait_time
        """
        # Step 1: Create request
        request_id = self.create_video_request(source_info, output_config, filters)

        # Step 2: Accept request and get upload URL
        accept_response = self.accept_video_request(request_id)

        # Extract upload URL from the response structure: {"uploadId": "...", "urls": [url1, url2, ...]}
        urls = accept_response.get("urls", [])
        upload_url = urls[0] if urls else None

        if not upload_url:
            raise unexpected_response_error("the response has no upload URL", accept_response, request_id=request_id)

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
                    return self.download_file(download_url, "Downloading the processed video", request_id=request_id)
                else:
                    raise unexpected_response_error(
                        "the completed job has no download URL", status, request_id=request_id
                    )

            elif current_status == "failed":
                raise job_failed_error(status.get("message"), status, request_id=request_id)

            # Wait before next poll
            time.sleep(poll_interval)

        raise job_timeout_error(max_wait_time, request_id=request_id)
