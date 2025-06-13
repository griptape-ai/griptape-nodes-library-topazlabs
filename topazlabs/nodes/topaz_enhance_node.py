"""Topaz Labs Enhance Node for improving image sharpness and clarity."""

import sys
import os
from typing import Any

# Add parent directory to path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from nodes.base_topaz_node import BaseTopazNode
from utils.constants import ENHANCE_MODELS, ENHANCE_DEFAULTS, PARAMETER_RANGES


class TopazEnhanceNode(BaseTopazNode):
    """Node for enhancing image sharpness, clarity, and restoring facial details using Topaz Labs Enhance API."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the Topaz Enhance node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        
        # Model selection
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="Enhancement model preset. Standard V2 for balanced enhancement, High Fidelity V2 for preserving detail, Low Resolution V2 for web images.",
                type=ParameterTypeBuiltin.STR.value,
                default_value=ENHANCE_DEFAULTS["model"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=ENHANCE_MODELS)},
                ui_options={"display_name": "Enhancement Model"}
            )
        )
        
        # Sharpen parameter
        sharpen_range = PARAMETER_RANGES["sharpen"]
        self.add_parameter(
            Parameter(
                name="sharpen",
                tooltip="Optional additional sharpening (0.0 - 1.0). 0 means no extra sharpening beyond the model's default.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_DEFAULTS["sharpen"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=sharpen_range[0], max_val=sharpen_range[1])},
                ui_options={
                    "display_name": "Sharpen",
                    "step": 0.01
                }
            )
        )
        
        # Denoise parameter
        denoise_range = PARAMETER_RANGES["denoise"]
        self.add_parameter(
            Parameter(
                name="denoise",
                tooltip="Optional denoising during enhancement (0.0 - 1.0). Useful for images with noise that should be cleaned up.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_DEFAULTS["denoise"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=denoise_range[0], max_val=denoise_range[1])},
                ui_options={
                    "display_name": "Denoise",
                    "step": 0.01
                }
            )
        )
        
        # Fix compression parameter
        fix_compression_range = PARAMETER_RANGES["fix_compression"]
        self.add_parameter(
            Parameter(
                name="fix_compression",
                tooltip="Fix lossy image artifacts from JPEG compression (0.0 - 1.0). Higher values more aggressively fix compression artifacts.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_DEFAULTS["fix_compression"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=fix_compression_range[0], max_val=fix_compression_range[1])},
                ui_options={
                    "display_name": "Fix Compression",
                    "step": 0.01
                }
            )
        )
        
        # Face enhancement toggle
        self.add_parameter(
            Parameter(
                name="face_enhancement",
                tooltip="Enable face-specific enhancements for better facial detail restoration.",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=ENHANCE_DEFAULTS["face_enhancement"],
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Face Enhancement"}
            )
        )
        
        # Face enhancement strength
        face_strength_range = PARAMETER_RANGES["face_enhancement_strength"]
        self.add_parameter(
            Parameter(
                name="face_enhancement_strength",
                tooltip="How strong facial enhancement should be (0.0 - 1.0). Only applies when Face Enhancement is enabled.",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_DEFAULTS["face_enhancement_strength"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=face_strength_range[0], max_val=face_strength_range[1])},
                ui_options={
                    "display_name": "Face Enhancement Strength",
                    "step": 0.01
                }
            )
        )
    
    def process(self) -> None:
        """Process the image using Topaz Labs Enhance API."""
        try:
            # Update status
            self._update_status("Starting image enhancement...", show=True)
            
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
            sharpen = self.get_parameter_value("sharpen")
            denoise = self.get_parameter_value("denoise")
            fix_compression = self.get_parameter_value("fix_compression")
            face_enhancement = self.get_parameter_value("face_enhancement")
            face_enhancement_strength = self.get_parameter_value("face_enhancement_strength")
            output_format = self.get_parameter_value("output_format")
            
            # Prepare API parameters
            api_params = {
                "model": model,
                "output_format": output_format
            }
            
            # Add optional parameters only if they have meaningful values
            if sharpen and sharpen > 0:
                api_params["sharpen"] = sharpen
            
            if denoise and denoise > 0:
                api_params["denoise"] = denoise
                
            if fix_compression and fix_compression > 0:
                api_params["fix_compression"] = fix_compression
            
            # Add face enhancement parameters if enabled
            if face_enhancement:
                api_params["face_enhancement"] = True
                if face_enhancement_strength is not None:
                    api_params["face_enhancement_strength"] = face_enhancement_strength
            
            # Update status
            enhancement_type = "with face enhancement" if face_enhancement else "standard"
            self._update_status(f"Processing with {model} model ({enhancement_type})...", show=True)
            
            # Create API client and make request
            with self._get_topaz_client() as client:
                processed_image_data = client.enhance(
                    image_data=image_data,
                    **api_params
                )
            
            # Save output image
            self._update_status("Saving enhanced image...", show=True)
            output_artifact = self._save_image_output(
                processed_image_data, 
                filename_hint="enhanced_image"
            )
            
            # Set output parameter
            self.parameter_output_values["image_output"] = output_artifact
            
            # Update status with success
            self._update_status("Image enhancement completed successfully!", show=True)
            
        except Exception as e:
            error_message = f"Error during enhancement: {str(e)}"
            self._update_status(error_message, show=True)
            raise Exception(error_message)
    
    def validate_node(self) -> list[Exception] | None:
        """Validate the enhance node configuration.
        
        Returns:
            List of validation errors, or None if valid
        """
        errors = super().validate_node() or []
        
        # Validate parameter ranges
        params_to_validate = [
            ("sharpen", "sharpen"),
            ("denoise", "denoise"), 
            ("fix_compression", "fix_compression"),
            ("face_enhancement_strength", "face_enhancement_strength")
        ]
        
        for param_name, range_key in params_to_validate:
            value = self.get_parameter_value(param_name)
            if value is not None:
                param_range = PARAMETER_RANGES[range_key]
                if not (param_range[0] <= value <= param_range[1]):
                    display_name = param_name.replace("_", " ").title()
                    errors.append(ValueError(f"{display_name} must be between {param_range[0]} and {param_range[1]}"))
        
        return errors if errors else None 