"""Node for Topaz Labs denoising operations."""

from typing import Dict, Any, Optional
from griptape.artifacts import ImageArtifact
from griptape_nodes.exe_types.node_types import DataNode, BaseNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from base_topaz_node import BaseTopazNode
from constants import DENOISE_MODELS, DENOISE_DEFAULTS, PARAMETER_RANGES


class TopazDenoiseNode(BaseTopazNode):
    """Node for reducing image noise using Topaz Labs Denoise API."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the Topaz Denoise node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        
        # Model selection
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="Denoise model preset. Normal for light noise, Strong for moderate noise, Extreme for heavy noise.",
                type=ParameterTypeBuiltin.STR.value,
                default_value=DENOISE_DEFAULTS["model"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=DENOISE_MODELS)},
                ui_options={"display_name": "Denoise Model"}
            )
        )
        
        # Strength parameter
        strength_range = PARAMETER_RANGES["strength"]
        self.add_parameter(
            Parameter(
                name="strength",
                tooltip="How aggressive the noise reduction should be (0.01 - 1.0). Higher values remove more noise but may also remove fine details.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=DENOISE_DEFAULTS["strength"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=strength_range[0], max_val=strength_range[1])},
                ui_options={
                    "display_name": "Strength",
                    "step": 0.01
                }
            )
        )
        
        # Minor deblur parameter
        minor_deblur_range = PARAMETER_RANGES["minor_deblur"]
        self.add_parameter(
            Parameter(
                name="minor_deblur",
                tooltip="Mild sharpening applied after noise reduction (0.01 - 1.0). Helps restore sharpness lost during denoising.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=DENOISE_DEFAULTS["minor_deblur"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=minor_deblur_range[0], max_val=minor_deblur_range[1])},
                ui_options={
                    "display_name": "Minor Deblur",
                    "step": 0.01
                }
            )
        )
        
        # Original detail parameter
        original_detail_range = PARAMETER_RANGES["original_detail"]
        self.add_parameter(
            Parameter(
                name="original_detail",
                tooltip="Restore fine texture lost during denoising (0.0 - 1.0). Higher values preserve more original detail but may retain some noise.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=DENOISE_DEFAULTS["original_detail"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=original_detail_range[0], max_val=original_detail_range[1])},
                ui_options={
                    "display_name": "Original Detail",
                    "step": 0.01
                }
            )
        )
    
    async def _process_async(self) -> None:
        """Process the image using Topaz Labs Denoise API."""
        try:
            # Update status
            self._update_status("Starting image denoising...", show=True)
            
            # Get input image
            image_artifact = self.get_parameter_value("image_input")
            
            # Debug: Check what we got
            if image_artifact is None:
                # Check if there's a connection but no value
                input_param = self.get_parameter_by_name("image_input")
                if input_param and hasattr(input_param, 'connections'):
                    self._update_status("Image parameter exists but no value received - checking connections...", show=True)
                else:
                    self._update_status("No image input parameter or connections found", show=True)
                raise ValueError("No input image provided")
            
            if not image_artifact:
                raise ValueError("Input image is empty or falsy")
            
            # Debug: Log the type and basic info about the image artifact
            artifact_type = type(image_artifact).__name__
            self._update_status(f"Received {artifact_type} for processing", show=True)
            
            # Extract image data
            image_data = self._get_image_data(image_artifact)
            
            # Gather parameters
            model = self.get_parameter_value("model")
            strength = self.get_parameter_value("strength")
            minor_deblur = self.get_parameter_value("minor_deblur")
            original_detail = self.get_parameter_value("original_detail")
            output_format = self.get_parameter_value("output_format")
            
            # Update status
            self._update_status(f"Processing with {model} model...", show=True)
            
            # Create API client and make request
            with self._get_topaz_client() as client:
                processed_image_data = client.denoise(
                    image_data=image_data,
                    model=model,
                    strength=strength,
                    minor_deblur=minor_deblur,
                    original_detail=original_detail,
                    output_format=output_format
                )
            
            # Save output image
            self._update_status("Saving processed image...", show=True)
            output_artifact = self._save_image_output(
                processed_image_data, 
                filename_hint="denoised_image"
            )
            
            # Set output parameter
            self.parameter_output_values["image_output"] = output_artifact
            
            # Update status with success
            self._update_status("Image denoising completed successfully!", show=True)
            
        except Exception as e:
            error_message = f"Error during denoising: {str(e)}"
            self._update_status(error_message, show=True)
            raise Exception(error_message)
    
    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate the denoise node configuration before execution.
        
        Returns:
            List of validation errors, or None if valid
        """
        errors = super().validate_before_node_run() or []
        
        # Validate parameter ranges
        strength = self.get_parameter_value("strength")
        if strength is not None:
            strength_range = PARAMETER_RANGES["strength"]
            if not (strength_range[0] <= strength <= strength_range[1]):
                errors.append(ValueError(f"Strength must be between {strength_range[0]} and {strength_range[1]}"))
        
        minor_deblur = self.get_parameter_value("minor_deblur")
        if minor_deblur is not None:
            minor_deblur_range = PARAMETER_RANGES["minor_deblur"]
            if not (minor_deblur_range[0] <= minor_deblur <= minor_deblur_range[1]):
                errors.append(ValueError(f"Minor deblur must be between {minor_deblur_range[0]} and {minor_deblur_range[1]}"))
        
        original_detail = self.get_parameter_value("original_detail")
        if original_detail is not None:
            original_detail_range = PARAMETER_RANGES["original_detail"]
            if not (original_detail_range[0] <= original_detail <= original_detail_range[1]):
                errors.append(ValueError(f"Original detail must be between {original_detail_range[0]} and {original_detail_range[1]}"))
        
        return errors if errors else None
    
    def validate_before_workflow_run(self) -> list[Exception] | None:
        return self.validate_before_node_run() 