"""HTTP client for Topaz Labs API."""

import os
import sys
import time
from typing import Any, BinaryIO, cast

import requests
from griptape_nodes.exe_types.core_types import NodeError

# Add current directory to path for constants import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from constants import API_BASE_URL, API_KEY_ENV_VAR, VIDEO_API_BASE_URL
from topaz_errors import PROVIDER, Fields, job_error

STORAGE_PROVIDER = f"{PROVIDER} file storage"


def _api_error(exc: requests.RequestException, fields: Fields | None = None) -> NodeError:
    """The error for a failed call to the Topaz Labs API. Only a 401 means the key was refused."""
    status = getattr(exc.response, "status_code", None)
    return NodeError.from_request_exception(
        exc, provider=PROVIDER, secret_name=API_KEY_ENV_VAR, key_refused=status == 401, fields=fields
    )


def _read_json(response: requests.Response, fields: Fields | None = None) -> dict[str, Any]:
    """The JSON object in a 2xx response, or a NodeError for HTML, an empty body or a JSON list."""
    try:
        body = response.json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        raise NodeError.from_http_response(response, provider=PROVIDER, key_refused=False, fields=fields)
    return body


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
            NodeError: If a request fails, the job fails, or the job doesn't complete within max_wait_time.
        """
        # Step 1: Start the async job
        start_response = cast(
            dict[str, Any], self._make_request("enhance-gen/async", image_data, returns_json=True, **params)
        )
        process_id = start_response.get("process_id")
        if not process_id:
            raise job_error("Topaz Labs did not return a job ID. Run the node again.", response=start_response)

        # Step 2: Poll for completion
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_response = self.get_status(process_id)
            status = status_response.get("status")

            if status == "Completed":
                # Step 3: Download the result
                return self.download_output(process_id)
            elif status == "Failed":
                reason = status_response.get("message") or "Topaz Labs could not process the image."
                raise job_error(str(reason), response=status_response, job_id=process_id)

            time.sleep(poll_interval)

        raise job_error(
            f"Topaz Labs did not finish the image within {max_wait_time} seconds. Run the node again.",
            job_id=process_id,
        )

    def get_status(self, process_id: str) -> dict[str, Any]:
        """Get the status of a job."""
        url = f"{self.base_url}/status/{process_id}"
        return self._get_json(url, {"job_id": process_id}, headers={"Accept": "application/json"})

    def download_output(self, process_id: str) -> bytes:
        """Download the output of a completed job."""
        # Get the download URL
        url = f"{self.base_url}/download/{process_id}"
        fields: Fields = {"job_id": process_id}
        download_info = self._get_json(url, fields, headers={"Accept": "application/json"})
        download_url = download_info.get("download_url")

        if not download_url:
            raise job_error(
                "Topaz Labs did not return a download URL. Run the node again.",
                response=download_info,
                job_id=process_id,
            )

        # Download the actual image from the presigned URL
        return self.download_file(download_url, fields, timeout=300)

    def download_file(self, url: str, fields: Fields | None = None, timeout: int = 600) -> bytes:
        """Download a result from a signed storage URL.

        Every download goes through here, so a stalled or refused download reads the same everywhere.
        The signed URL carries its own authorization, so a 403 is not an API key problem.
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise NodeError.from_request_exception(
                e, provider=STORAGE_PROVIDER, key_refused=False, fields=fields
            ) from e
        return response.content

    def _send(self, method: str, url: str, fields: Fields | None = None, **kwargs) -> requests.Response:
        """Send a request to the Topaz Labs API, turning any failure into a NodeError."""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.RequestException as e:
            raise _api_error(e, fields) from e
        return response

    def _get_json(self, url: str, fields: Fields | None = None, **kwargs) -> dict[str, Any]:
        return _read_json(self._send("GET", url, fields, timeout=30, **kwargs), fields)

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
            NodeError: If the API request fails or answers with something other than an image or JSON
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

        response = self._send(
            "POST",
            url,
            files=files,
            data=form_data,
            headers=headers,
            timeout=300,  # 5 minute timeout for processing
        )

        if returns_json:
            return _read_json(response)

        # Validate response content type
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise NodeError.from_http_response(response, provider=PROVIDER, key_refused=False)

        return response.content

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
            NodeError: If the API request fails or returns no request ID
        """
        url = f"{VIDEO_API_BASE_URL}/"

        request_data = {"source": source_info, "output": output_config, "filters": filters}

        response = self._send("POST", url, json=request_data, headers={"Content-Type": "application/json"}, timeout=30)
        result = _read_json(response)
        request_id = result.get("requestId")

        if not request_id:
            raise job_error("Topaz Labs did not return a request ID. Run the node again.", response=result)

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
        fields: Fields = {"request_id": request_id}
        response = self._send("PATCH", f"{VIDEO_API_BASE_URL}/{request_id}/accept", fields, timeout=30)
        return _read_json(response, fields)

    def upload_video(
        self, upload_url: str, video_data: bytes, content_type: str = "video/mp4", request_id: str | None = None
    ) -> str:
        """Upload video data to the provided S3 URL.

        Args:
            upload_url: S3 upload URL from accept_video_request
            video_data: Video file data as bytes
            content_type: MIME type of the video file
            request_id: The video processing request ID, attached to any error

        Returns:
            ETag from the S3 upload response

        Raises:
            NodeError: If the upload fails or returns no ETag
        """
        fields: Fields = {"request_id": request_id} if request_id else {}
        try:
            response = requests.put(
                upload_url,
                data=video_data,
                headers={"Content-Type": content_type},
                timeout=600,  # 10 minutes for upload
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NodeError.from_request_exception(
                e, provider=STORAGE_PROVIDER, key_refused=False, fields=fields
            ) from e

        # Extract ETag from response headers
        etag = response.headers.get("ETag", "").strip('"')
        if not etag:
            raise job_error("Topaz Labs file storage did not return an ETag for the upload.", request_id=request_id)

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
            "PATCH",
            url,
            {"request_id": request_id},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
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
        return self._get_json(f"{VIDEO_API_BASE_URL}/{request_id}/status", {"request_id": request_id})
