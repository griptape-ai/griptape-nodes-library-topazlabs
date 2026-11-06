"""Topaz Labs Video Denoising Node for noise reduction and compression artifact removal."""

from typing import Any

from base_topaz_video_node import BaseTopazVideoNode
from griptape.artifacts import UrlArtifact
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider


class VideoUrlArtifact(UrlArtifact):
    """
    Artifact that contains a URL to a video.
    """

    def __init__(self, url: str, name: str | None = None):
        super().__init__(value=url, name=name or self.__class__.__name__)


class TopazVideoDenoiseNode(BaseTopazVideoNode):
    """Node for video denoising and compression artifact removal using Topaz Labs Video API."""

    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the video denoising node."""
        super().__init__(name, metadata)

        # Model selection (focused on denoising models)
        denoising_models = [
            "nyx-3",  # Advanced motion processing with auto denoising
            "ddv-3",  # Digital video denoising
            "dtd-4",  # Digital temporal denoising
            "dtds-2",  # Digital temporal denoising specialized
            "dtv-4",  # Digital temporal video processing
            "dtvs-2",  # Digital temporal video specialized
            "chf-3",  # Compression artifact removal
            "chr-2",  # Compression recovery
        ]

        self.add_parameter(
            Parameter(
                name="model",
                tooltip="AI model for video denoising",
                type=ParameterTypeBuiltin.STR.value,
                default_value="nyx-3",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Options(choices=denoising_models)},
                ui_options={"display_name": "Denoising Model"},
            )
        )

        # Auto processing mode
        self.add_parameter(
            Parameter(
                name="auto_mode",
                tooltip="Use automatic processing based on content analysis",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=True,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                ui_options={"display_name": "Auto Mode"},
            )
        )

        # Auto processing type
        auto_types = ["Relative", "Absolute", "Custom"]
        self.add_parameter(
            Parameter(
                name="auto_type",
                tooltip="Type of automatic processing when auto mode is enabled",
                type=ParameterTypeBuiltin.STR.value,
                default_value="Relative",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Options(choices=auto_types)},
                ui_options={"display_name": "Auto Type"},
            )
        )

        # Noise reduction intensity
        self.add_parameter(
            Parameter(
                name="noise_intensity",
                tooltip="Noise reduction intensity (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.5,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Noise Intensity", "step": 0.01},
            )
        )

        # Compression artifact removal
        self.add_parameter(
            Parameter(
                name="compression_recovery",
                tooltip="Remove compression artifacts (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.3,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Compression Recovery", "step": 0.01},
            )
        )

        # Detail preservation
        self.add_parameter(
            Parameter(
                name="detail_preservation",
                tooltip="Preserve fine details during denoising (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.7,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Detail Preservation", "step": 0.01},
            )
        )

        # Temporal consistency
        self.add_parameter(
            Parameter(
                name="temporal_consistency",
                tooltip="Maintain consistency across frames (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.8,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Temporal Consistency", "step": 0.01},
            )
        )

        # Sharpening (mild)
        self.add_parameter(
            Parameter(
                name="sharpen",
                tooltip="Mild sharpening to counteract softening (0.0 = none, 1.0 = maximum)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.1,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={"display_name": "Sharpening", "step": 0.01},
            )
        )

        # Add output parameters in the correct order
        self._add_output_parameters()

    def _build_source_info(self, video_bytes: bytes) -> dict[str, Any]:
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
            "frameRate": 30,  # Placeholder - would need video analysis
            "frameCount": 300,  # Placeholder - would need video analysis
        }

    def _build_filters(self) -> list[dict[str, Any]]:
        """Build filter configuration for video denoising.

        Returns:
            List of filter configurations
        """
        model = self.get_parameter_value("model") or "nyx-3"
        auto_mode = self.get_parameter_value("auto_mode")
        auto_type = self.get_parameter_value("auto_type") or "Relative"
        noise_intensity = self.get_parameter_value("noise_intensity") or 0.5
        compression_recovery = self.get_parameter_value("compression_recovery") or 0.3
        detail_preservation = self.get_parameter_value("detail_preservation") or 0.7
        temporal_consistency = self.get_parameter_value("temporal_consistency") or 0.8
        sharpen = self.get_parameter_value("sharpen") or 0.1

        filter_config = {"model": model}

        # Add auto processing if enabled
        if auto_mode:
            filter_config["auto"] = auto_type

        # Add manual parameters if not using auto mode or for fine-tuning
        if not auto_mode or model in ["nyx-3", "ddv-3"]:
            if noise_intensity > 0:
                filter_config["noise"] = noise_intensity

            if compression_recovery > 0:
                filter_config["compression"] = compression_recovery

            if detail_preservation > 0:
                filter_config["details"] = detail_preservation

            if sharpen > 0:
                filter_config["sharpen"] = sharpen

            # Add temporal consistency for temporal models
            if model in ["dtd-4", "dtds-2", "dtv-4", "dtvs-2"] and temporal_consistency > 0:
                filter_config["temporalConsistency"] = temporal_consistency

        return [filter_config]

    async def _process_async(self) -> None:
        """Process the video with denoising and artifact removal."""
        try:
            self._update_status("Starting video denoising...", show=True)

            # Get input video
            video_input = self.get_parameter_value("video_input")

            # Extract video data
            video_bytes = self._get_video_data(video_input)

            # Get Topaz client
            client = self._get_topaz_client()
            self._update_status("Connected to Topaz Labs API", show=True)

            # Build request configuration
            source_info = self._build_source_info(video_bytes)
            output_config = self._get_output_config()

            # Keep original resolution and frame rate
            output_config["resolution"] = source_info["resolution"]
            output_config["frameRate"] = source_info["frameRate"]

            filters = self._build_filters()

            model = self.get_parameter_value("model") or "nyx-3"
            auto_mode = self.get_parameter_value("auto_mode")
            mode_text = "Auto" if auto_mode else "Manual"

            self._update_status(f"Denoising with {model} model ({mode_text} mode)...", show=True)

            # Get processing timeout in seconds
            timeout_minutes = self.get_parameter_value("processing_timeout") or 60
            timeout_seconds = timeout_minutes * 60

            processed_video_bytes = await self._run_video_job(
                client, video_bytes, source_info, output_config, filters, timeout_seconds
            )

            self._update_status("Saving denoised video...", show=True)

            # Save output video
            output_artifact = self._save_video_output(processed_video_bytes, f"denoised_{model}_{mode_text.lower()}")

            # Set outputs
            self.parameter_output_values["video_output"] = output_artifact
            # task_id already set above with the actual request ID

            self._update_status(f"Video denoising completed successfully! ({model} in {mode_text} mode)", show=True)

        except Exception as e:
            error_msg = f"Video denoising failed: {str(e)}"
            self._update_status(error_msg, show=True)
            raise
