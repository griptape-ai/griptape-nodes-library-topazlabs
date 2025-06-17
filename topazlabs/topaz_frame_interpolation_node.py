"""Topaz Labs Frame Interpolation Node for smooth motion and 60fps conversion."""

import time
from typing import Dict, Any
from griptape.artifacts import UrlArtifact
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from base_topaz_video_node import BaseTopazVideoNode


from constants import VIDEO_DEFAULTS, FRAME_RATES


class VideoUrlArtifact(UrlArtifact):
    """
    Artifact that contains a URL to a video.
    """

    def __init__(self, url: str, name: str | None = None):
        super().__init__(value=url, name=name or self.__class__.__name__)


class TopazFrameInterpolationNode(BaseTopazVideoNode):
    """Node for frame interpolation and smooth motion using Topaz Labs Video API."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the frame interpolation node."""
        super().__init__(name, metadata)
        
        # Model selection (focused on frame interpolation models)
        interpolation_models = [
            "apo-8",    # Popular 60fps conversion
            "gcg-5",    # General content generation
            "ghq-5",    # High-quality generation
            "iris-2",   # Intelligent resolution improvement
            "iris-3",   # Advanced resolution improvement
            "nxf-1",    # Next-gen frame processing
            "nyx-3"     # Advanced motion processing
        ]
        
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="AI model for frame interpolation",
                type=ParameterTypeBuiltin.STR.value,
                default_value="apo-8",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=interpolation_models)},
                ui_options={"display_name": "Interpolation Model"}
            )
        )
        
        # Target frame rate
        target_fps_options = ["60.0", "30.0", "24.0", "23.976", "25.0", "29.97", "50.0", "59.94", "120.0"]
        self.add_parameter(
            Parameter(
                name="target_fps",
                tooltip="Target output frame rate",
                type=ParameterTypeBuiltin.STR.value,
                default_value="60.0",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=target_fps_options)},
                ui_options={"display_name": "Target FPS"}
            )
        )
        
        # Slow motion factor
        self.add_parameter(
            Parameter(
                name="slowmo_factor",
                tooltip="Slow motion multiplier (1 = normal speed, 2 = 2x slower, etc.)",
                type=ParameterTypeBuiltin.INT.value,
                default_value=1,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=1, max_val=8)},
                ui_options={"display_name": "Slow Motion Factor"}
            )
        )
        
        # Duplicate frame removal
        self.add_parameter(
            Parameter(
                name="remove_duplicates",
                tooltip="Remove duplicate frames during processing",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=True,
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Remove Duplicate Frames"}
            )
        )
        
        # Duplicate detection threshold
        self.add_parameter(
            Parameter(
                name="duplicate_threshold",
                tooltip="Threshold for detecting duplicate frames (0.0 = strict, 1.0 = lenient)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.1,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Duplicate Threshold", "step": 0.01}
            )
        )
    
    def _build_source_info(self, video_bytes: bytes) -> Dict[str, Any]:
        """Build source video information for the API request.
        
        Args:
            video_bytes: Input video data
            
        Returns:
            Source information dictionary
        """
        # For now, we'll use reasonable defaults
        # In a production implementation, you might want to analyze the video file
        return {
            "container": "mp4",
            "size": len(video_bytes),
            # Note: In a real implementation, you'd analyze the video to get these values
            "resolution": {"width": 1920, "height": 1080},
            "duration": 10000,  # Placeholder - would need video analysis
            "frameRate": 30,    # Placeholder - would need video analysis
            "frameCount": 300   # Placeholder - would need video analysis
        }
    
    def _build_filters(self) -> list[Dict[str, Any]]:
        """Build filter configuration for frame interpolation.
        
        Returns:
            List of filter configurations
        """
        model = self.get_parameter_value("model") or "apo-8"
        target_fps = self.get_parameter_value("target_fps") or "60.0"
        slowmo_factor = self.get_parameter_value("slowmo_factor") or 1
        remove_duplicates = self.get_parameter_value("remove_duplicates")
        duplicate_threshold = self.get_parameter_value("duplicate_threshold") or 0.1
        
        filter_config = {
            "model": model,
            "fps": float(target_fps),
            "slowmo": slowmo_factor
        }
        
        # Add duplicate removal settings if enabled
        if remove_duplicates:
            filter_config.update({
                "duplicate": True,
                "duplicateThreshold": duplicate_threshold
            })
        
        return [filter_config]
    
    def process(self) -> None:
        """Process the video with frame interpolation."""
        try:
            self._update_status("Starting frame interpolation...", show=True)
            
            # Get input video
            video_input = self.get_parameter_value("video_input")
            if not video_input:
                raise ValueError("No input video provided")
            
            # Extract video data
            video_bytes = self._get_video_data(video_input)
            
            # Get Topaz client
            client = self._get_topaz_client()
            self._update_status("Connected to Topaz Labs API", show=True)
            
            # Build request configuration
            source_info = self._build_source_info(video_bytes)
            output_config = self._get_output_config()
            
            # Add resolution to output config (copy from source for now)
            output_config["resolution"] = source_info["resolution"]
            
            # Add frame rate to output config
            target_fps = self.get_parameter_value("target_fps") or "60.0"
            output_config["frameRate"] = float(target_fps)
            
            filters = self._build_filters()
            
            self._update_status("Submitting video for processing...", show=True)
            
            # Get processing timeout in seconds
            timeout_minutes = self.get_parameter_value("processing_timeout") or 60
            timeout_seconds = timeout_minutes * 60
            
            # Create request and get task ID
            request_id = client.create_video_request(source_info, output_config, filters)
            
            # Set the task ID output immediately
            self.parameter_output_values["task_id"] = request_id
            
            # Also try to publish the task ID update
            if hasattr(self, 'publish_update_to_parameter'):
                try:
                    self.publish_update_to_parameter("task_id", request_id)
                except:
                    pass
            
            self._update_status(f"Created processing request: {request_id}", show=True)
            
            # Accept request and get upload URL
            accept_response = client.accept_video_request(request_id)
            urls = accept_response.get("urls", [])
            upload_url = urls[0] if urls else None
            
            if not upload_url:
                raise ValueError(f"No upload URL in response. Response: {accept_response}")
            
            self._update_status("Uploading video to Topaz Labs...", show=True)
            
            # Upload video and get ETag
            etag = client.upload_video(upload_url, video_bytes)
            
            # Complete upload
            client.complete_video_upload(request_id, etag)
            self._update_status("Upload complete, processing started...", show=True)
            
            # Poll for completion with progress updates
            import time
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                status = client.get_video_status(request_id)
                
                current_status = status.get("status", "unknown")
                progress_percent = status.get("progress", 0)
                status_message = status.get("message", f"Processing... (status: {current_status})")
                
                # Update progress and status only if API provides progress
                if progress_percent > 0:
                    self._update_progress(round(progress_percent))
                self._update_status(status_message, show=True)
                
                if current_status == "complete":
                    self._update_status("Processing complete, downloading result...", show=True)
                    
                    download_info = status.get("download", {})
                    download_url = download_info.get("url")
                    
                    if download_url:
                        # Download the processed video
                        import requests
                        download_response = requests.get(download_url, timeout=600)
                        download_response.raise_for_status()
                        processed_video_bytes = download_response.content
                        break
                    else:
                        raise ValueError("No download URL in completion response")
                
                elif current_status == "failed":
                    error_message = status.get("message", "Processing failed")
                    raise Exception(f"Video processing failed: {error_message}")
                
                # Wait before next poll
                time.sleep(15)
            else:
                raise TimeoutError(f"Video processing did not complete within {timeout_seconds} seconds")
            
            self._update_status("Saving processed video...", show=True)
            
            # Save output video
            output_artifact = self._save_video_output(
                processed_video_bytes, 
                f"frame_interpolated_{self.get_parameter_value('model')}"
            )
            
            # Set outputs
            self.parameter_output_values["video_output"] = output_artifact
            
            self._update_status("Frame interpolation completed successfully!", show=True)
            
        except Exception as e:
            error_msg = f"Frame interpolation failed: {str(e)}"
            self._update_status(error_msg, show=True)
            raise Exception(error_msg) 