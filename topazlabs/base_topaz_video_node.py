"""Base node for Topaz Labs video operations."""

import asyncio
import hashlib
import time
from typing import Dict, Any, Optional
from griptape.artifacts import UrlArtifact, BlobArtifact

from griptape_nodes.exe_types.node_types import ControlNode, AsyncResult
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from constants import SERVICE, API_KEY_ENV_VAR, VIDEO_CONTAINERS, VIDEO_CODECS, AUDIO_CODECS, AUDIO_TRANSFER_MODES, VIDEO_PROFILES, COMPRESSION_LEVELS, AUDIO_BITRATES
from topaz_client import TopazClient


class VideoUrlArtifact(UrlArtifact):
    """
    Artifact that contains a URL to a video.
    """

    def __init__(self, url: str, name: str | None = None):
        super().__init__(value=url, name=name or self.__class__.__name__)


class BaseTopazVideoNode(ControlNode):
    """Base class for all Topaz Labs video processing nodes."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the base Topaz video node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        
        # Video input parameter
        self.add_parameter(
            Parameter(
                name="video_input",
                tooltip="Input video to process",
                type="VideoUrlArtifact",
                input_types=["VideoUrlArtifact", "BlobArtifact", "VideoArtifact"],
                allowed_modes={ParameterMode.INPUT},
                ui_options={"display_name": "Input Video"}
            )
        )
        
        # Output container format
        self.add_parameter(
            Parameter(
                name="output_container",
                tooltip="Output video container format",
                type=ParameterTypeBuiltin.STR.value,
                default_value="mp4",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=VIDEO_CONTAINERS)},
                ui_options={"display_name": "Container Format"}
            )
        )
        
        # Video encoder
        self.add_parameter(
            Parameter(
                name="video_encoder",
                tooltip="Video encoding codec",
                type=ParameterTypeBuiltin.STR.value,
                default_value="H265",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=VIDEO_CODECS)},
                ui_options={"display_name": "Video Encoder"}
            )
        )
        
        # Video profile
        self.add_parameter(
            Parameter(
                name="video_profile",
                tooltip="Video encoding profile",
                type=ParameterTypeBuiltin.STR.value,
                default_value="Main",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=VIDEO_PROFILES)},
                ui_options={"display_name": "Video Profile"}
            )
        )
        
        # Audio codec
        self.add_parameter(
            Parameter(
                name="audio_codec",
                tooltip="Audio encoding codec",
                type=ParameterTypeBuiltin.STR.value,
                default_value="AAC",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=AUDIO_CODECS)},
                ui_options={"display_name": "Audio Codec"}
            )
        )
        
        # Audio transfer mode
        self.add_parameter(
            Parameter(
                name="audio_transfer",
                tooltip="How to handle audio during processing",
                type=ParameterTypeBuiltin.STR.value,
                default_value="Copy",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=AUDIO_TRANSFER_MODES)},
                ui_options={"display_name": "Audio Transfer"}
            )
        )
        
        # Audio bitrate
        self.add_parameter(
            Parameter(
                name="audio_bitrate",
                tooltip="Audio bitrate in kbps",
                type=ParameterTypeBuiltin.STR.value,
                default_value="320",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=AUDIO_BITRATES)},
                ui_options={"display_name": "Audio Bitrate (kbps)"}
            )
        )
        
        # Compression level
        self.add_parameter(
            Parameter(
                name="compression_level",
                tooltip="Dynamic compression level for encoding",
                type=ParameterTypeBuiltin.STR.value,
                default_value="High",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=COMPRESSION_LEVELS)},
                ui_options={"display_name": "Compression Level"}
            )
        )
        
        # Crop to fit
        self.add_parameter(
            Parameter(
                name="crop_to_fit",
                tooltip="Crop video to fit output resolution",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=False,
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Crop to Fit"}
            )
        )
        
        # Processing timeout
        self.add_parameter(
            Parameter(
                name="processing_timeout",
                tooltip="Maximum time to wait for processing (minutes)",
                type=ParameterTypeBuiltin.INT.value,
                default_value=60,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=5, max_val=180)},
                ui_options={"display_name": "Timeout (minutes)"}
            )
        )
        
        # Status message for user feedback
        self.add_parameter(
            Parameter(
                name="status",
                tooltip="Processing status and messages",
                type="str",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "multiline": True,
                    "hide": False,
                    "display_name": "Status",
                    "placeholder_text": "Status messages"
                }
            )
        )
        
        # Progress output
        self.add_parameter(
            Parameter(
                name="progress",
                tooltip="Processing progress percentage",
                type=ParameterTypeBuiltin.INT.value,
                default_value=0,
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "display_name": "Progress (%)",
                    "pulse_on_run": True
                }
            )
        )
        
        # Task ID output for advanced users
        self.add_parameter(
            Parameter(
                name="task_id",
                tooltip="Topaz Labs task ID for this processing job",
                type=ParameterTypeBuiltin.STR.value,
                default_value="",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"display_name": "Task ID"}
            )
        )
        
        # Video output parameter
        self.add_parameter(
            Parameter(
                name="video_output",
                tooltip="Processed video output",
                type="VideoUrlArtifact",
                output_type="VideoUrlArtifact",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "display_name": "Output Video",
                    "pulse_on_run": True
                }
            )
        )
    
    def _get_api_key(self) -> str:
        """Retrieve the API key from configuration.
        
        Returns:
            The Topaz Labs API key
            
        Raises:
            ValueError: If API key is not found
        """
        api_key = GriptapeNodes.SecretsManager().get_secret(API_KEY_ENV_VAR)
        if not api_key:
            raise ValueError(f"API key not found. Please set the {API_KEY_ENV_VAR} environment variable.")
        return api_key
    
    def _get_topaz_client(self) -> TopazClient:
        """Create and return a Topaz Labs API client.
        
        Returns:
            Configured TopazClient instance
            
        Raises:
            ValueError: If API key is not available
        """
        api_key = self._get_api_key()
        return TopazClient(api_key)
    
    def _get_video_data(self, video_artifact: Any) -> bytes:
        """Extract video data from artifact.
        
        Args:
            video_artifact: VideoUrlArtifact, BlobArtifact, or VideoArtifact
            
        Returns:
            Video data as bytes
            
        Raises:
            ValueError: If video artifact is invalid or unsupported
        """
        if not video_artifact:
            raise ValueError("No input video provided")
        
        try:
            # Extract video bytes
            if isinstance(video_artifact, (VideoUrlArtifact, BlobArtifact)):
                video_bytes = video_artifact.to_bytes()
            elif hasattr(video_artifact, 'to_bytes'):
                # Handle VideoArtifact or other artifact types with to_bytes method
                video_bytes = video_artifact.to_bytes()
            else:
                # Try to convert to bytes if it's a different artifact type
                video_bytes = video_artifact.to_bytes()
            
            # Verify we have video data
            if not video_bytes or len(video_bytes) < 1000:
                raise ValueError("Video data is empty or too small")
            
            # Create hash to track video changes
            video_hash = hashlib.md5(video_bytes).hexdigest()[:8]
            video_size = len(video_bytes)
            
            # Debug info
            if hasattr(video_artifact, 'value'):
                video_id = str(video_artifact.value)[:50] + "..." if len(str(video_artifact.value)) > 50 else str(video_artifact.value)
            else:
                video_id = f"hash_{video_hash}"
            
            self._update_status(f"Processing: {video_id} ({video_size} bytes, hash: {video_hash})", show=True)
            
            return video_bytes
            
        except Exception as e:
            raise ValueError(f"Failed to extract video data: {str(e)}")
    
    def _save_video_output(self, video_data: bytes, filename_hint: str = "processed_video") -> VideoUrlArtifact:
        """Save processed video data and create output artifact.
        
        Args:
            video_data: Binary video data
            filename_hint: Hint for the filename
            
        Returns:
            VideoUrlArtifact pointing to the saved video
            
        Raises:
            Exception: If saving fails
        """
        try:
            # Import inside method to avoid caching issues
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
            
            # Get output format
            output_container = self.get_parameter_value("output_container") or "mp4"
            
            # Generate unique filename with timestamp and hash
            timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
            content_hash = hashlib.md5(video_data).hexdigest()[:8]  # Short hash of content
            filename = f"{filename_hint}_{timestamp}_{content_hash}.{output_container.lower()}"
            
            # Save to managed file location and get URL
            static_url = GriptapeNodes.StaticFilesManager().save_static_file(
                video_data, filename
            )
            
            return VideoUrlArtifact(
                url=static_url, name=f"{filename_hint}_{timestamp}"
            )
            
        except Exception as e:
            raise Exception(f"Failed to save output video: {str(e)}")
    
    def _update_status(self, message: str, show: bool = True) -> None:
        """Update the status parameter with a message.
        
        Args:
            message: Status message to display
            show: Whether to show the status parameter in UI
        """
        current_status = self.get_parameter_value("status") or ""
        timestamp = time.strftime("%H:%M:%S")
        new_message = f"[{timestamp}] {message}"
        
        if current_status:
            updated_status = f"{current_status}\n{new_message}"
        else:
            updated_status = new_message
        
        self.set_parameter_value("status", updated_status)
        
        # Show/hide the status parameter
        status_param = self.get_parameter_by_name("status")
        if status_param and hasattr(status_param, '_ui_options'):
            status_param._ui_options["hide"] = not show
    
    def _update_progress(self, progress: int) -> None:
        """Update the progress parameter.
        
        Args:
            progress: Progress percentage (0-100)
        """
        progress_value = max(0, min(100, progress))
        self.parameter_output_values["progress"] = progress_value
        
        # Also try to publish the update if the method exists
        if hasattr(self, 'publish_update_to_parameter'):
            try:
                self.publish_update_to_parameter("progress", progress_value)
            except:
                pass  # Fallback silently if method doesn't work
    
    def _get_output_config(self) -> Dict[str, Any]:
        """Build output configuration from node parameters.
        
        Returns:
            Output configuration dictionary for Topaz API
        """
        return {
            "container": self.get_parameter_value("output_container") or "mp4",
            "videoEncoder": self.get_parameter_value("video_encoder") or "H265",
            "videoProfile": self.get_parameter_value("video_profile") or "Main",
            "audioCodec": self.get_parameter_value("audio_codec") or "AAC",
            "audioTransfer": self.get_parameter_value("audio_transfer") or "Copy",
            "audioBitrate": self.get_parameter_value("audio_bitrate") or "320",
            "dynamicCompressionLevel": self.get_parameter_value("compression_level") or "High",
            "cropToFit": self.get_parameter_value("crop_to_fit") or False
        }
    
    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate the node configuration before execution.
        
        Returns:
            List of validation errors, or None if valid
        """
        errors = []
        
        # Check API key
        try:
            self._get_api_key()
        except ValueError as e:
            errors.append(e)
        
        # Check timeout value
        timeout = self.get_parameter_value("processing_timeout")
        if timeout and (timeout < 5 or timeout > 180):
            errors.append(ValueError("Processing timeout must be between 5 and 180 minutes"))
        
        return errors if errors else None
    
    def validate_before_workflow_run(self) -> list[Exception] | None:
        return self.validate_before_node_run()
    
    def process(self) -> AsyncResult[None]:
        """Non-blocking entry point for Griptape engine."""
        yield lambda: self._process_sync()
    
    def _process_sync(self) -> None:
        """Synchronous wrapper that runs async code."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_async())
        finally:
            loop.close()
    
    async def _process_async(self) -> None:
        """Abstract async process method - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the _process_async method") 