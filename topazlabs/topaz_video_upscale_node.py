"""Topaz Labs Video Upscaling Node for resolution enhancement and quality improvement."""

import time
from typing import Dict, Any
from griptape.artifacts import UrlArtifact
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from base_topaz_video_node import BaseTopazVideoNode


from constants import VIDEO_DEFAULTS


class VideoUrlArtifact(UrlArtifact):
    """
    Artifact that contains a URL to a video.
    """

    def __init__(self, url: str, name: str | None = None):
        super().__init__(value=url, name=name or self.__class__.__name__)


class TopazVideoUpscaleNode(BaseTopazVideoNode):
    """Node for video upscaling and quality enhancement using Topaz Labs Video API."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the video upscaling node."""
        super().__init__(name, metadata)
        
        # Model selection (focused on upscaling models)
        upscaling_models = [
            "prob-4",   # Professional broadcast quality
            "rhea-1",   # Generative AI upscaling (4x)
            "aaa-9",    # High-quality upscaling with detail enhancement
            "ahq-12",   # Archival quality upscaling
            "alq-13",   # Low-quality input optimization
            "amq-13",   # Medium-quality enhancement
            "apf-2",    # Professional film enhancement
            "rxl-1",    # Resolution excellence
            "thd-3",    # Texture and detail enhancement
            "thf-4",    # Texture high-fidelity
        ]
        
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="AI model for video upscaling",
                type=ParameterTypeBuiltin.STR.value,
                default_value="prob-4",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=upscaling_models)},
                ui_options={"display_name": "Upscaling Model"}
            )
        )
        
        # Upscale factor
        upscale_factors = ["2x", "4x", "Auto"]
        self.add_parameter(
            Parameter(
                name="upscale_factor",
                tooltip="Resolution upscaling factor",
                type=ParameterTypeBuiltin.STR.value,
                default_value="2x",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=upscale_factors)},
                ui_options={"display_name": "Upscale Factor"}
            )
        )
        
        # Detail enhancement
        self.add_parameter(
            Parameter(
                name="detail_enhancement",
                tooltip="Enhance fine details and textures (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.5,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Detail Enhancement", "step": 0.01}
            )
        )
        
        # Sharpening
        self.add_parameter(
            Parameter(
                name="sharpen",
                tooltip="Edge sharpening intensity (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Sharpening", "step": 0.01}
            )
        )
        
        # Noise reduction
        self.add_parameter(
            Parameter(
                name="noise_reduction",
                tooltip="Noise reduction intensity (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Noise Reduction", "step": 0.01}
            )
        )
        
        # Compression artifact removal
        self.add_parameter(
            Parameter(
                name="compression_recovery",
                tooltip="Remove compression artifacts (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Compression Recovery", "step": 0.01}
            )
        )
        
        # Focus fix
        self.add_parameter(
            Parameter(
                name="focus_fix",
                tooltip="Fix blur and focus issues (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Focus Fix", "step": 0.01}
            )
        )
        
        # Original detail recovery
        self.add_parameter(
            Parameter(
                name="original_detail_recovery",
                tooltip="Attempt to recover lost original details (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Original Detail Recovery", "step": 0.01}
            )
        )
        
        # Add output parameters in the correct order
        self._add_output_parameters()
    
    def _calculate_output_resolution(self, source_resolution: Dict[str, int]) -> Dict[str, int]:
        """Calculate output resolution based on upscale factor.
        
        Args:
            source_resolution: Source video resolution
            
        Returns:
            Target output resolution
        """
        upscale_factor = self.get_parameter_value("upscale_factor") or "2x"
        
        if upscale_factor == "4x":
            multiplier = 4
        elif upscale_factor == "2x":
            multiplier = 2
        else:  # Auto
            # For auto, use 2x as default
            multiplier = 2
        
        return {
            "width": source_resolution["width"] * multiplier,
            "height": source_resolution["height"] * multiplier
        }
    
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
        """Build filter configuration for video upscaling.
        
        Returns:
            List of filter configurations
        """
        model = self.get_parameter_value("model") or "prob-4"
        detail_enhancement = self.get_parameter_value("detail_enhancement") or 0.5
        sharpen = self.get_parameter_value("sharpen") or 0.0
        noise_reduction = self.get_parameter_value("noise_reduction") or 0.0
        compression_recovery = self.get_parameter_value("compression_recovery") or 0.0
        focus_fix = self.get_parameter_value("focus_fix") or 0.0
        original_detail_recovery = self.get_parameter_value("original_detail_recovery") or 0.0
        
        filter_config = {
            "model": model
        }
        
        # Add enhancement parameters if they're non-zero
        if detail_enhancement > 0:
            filter_config["details"] = detail_enhancement
        
        if sharpen > 0:
            filter_config["sharpen"] = sharpen
        
        if noise_reduction > 0:
            filter_config["noise"] = noise_reduction
        
        if compression_recovery > 0:
            filter_config["compression"] = compression_recovery
        
        if focus_fix > 0:
            filter_config["focusFixLevel"] = focus_fix
        
        if original_detail_recovery > 0:
            filter_config["recoverOriginalDetailValue"] = original_detail_recovery
        
        return [filter_config]
    
    async def _process_async(self) -> None:
        """Process the video with upscaling and enhancement."""
        try:
            self._update_status("Starting video upscaling...", show=True)
            
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
            
            # Calculate and set output resolution
            output_resolution = self._calculate_output_resolution(source_info["resolution"])
            output_config["resolution"] = output_resolution
            
            # Keep original frame rate
            output_config["frameRate"] = source_info["frameRate"]
            
            filters = self._build_filters()
            
            upscale_factor = self.get_parameter_value("upscale_factor") or "2x"
            model = self.get_parameter_value("model") or "prob-4"
            
            self._update_status(f"Upscaling with {model} model ({upscale_factor})...", show=True)
            
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
            
            # Poll for completion
            import asyncio
            import time
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                status = client.get_video_status(request_id)
                
                current_status = status.get("status", "unknown")
                status_message = status.get("message", f"Processing... (status: {current_status})")
                
                # Update status
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
                await asyncio.sleep(15)
            else:
                raise TimeoutError(f"Video processing did not complete within {timeout_seconds} seconds")
            
            self._update_status("Saving upscaled video...", show=True)
            
            # Save output video
            output_artifact = self._save_video_output(
                processed_video_bytes, 
                f"upscaled_{model}_{upscale_factor}"
            )
            
            # Set outputs
            self.parameter_output_values["video_output"] = output_artifact
            # task_id already set above with the actual request ID
            
            self._update_status(f"Video upscaling completed successfully! ({upscale_factor} with {model})", show=True)
            
        except Exception as e:
            error_msg = f"Video upscaling failed: {str(e)}"
            self._update_status(error_msg, show=True)
            raise Exception(error_msg) 