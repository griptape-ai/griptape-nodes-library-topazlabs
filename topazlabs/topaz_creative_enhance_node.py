"""Node for Topaz Labs creative enhancement operations."""

from typing import Dict, Any, Optional
from griptape.artifacts import ImageArtifact
from griptape_nodes.exe_types.node_types import DataNode, BaseNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from base_topaz_node import BaseTopazNode
from constants import ENHANCE_GENERATIVE_MODELS, ENHANCE_CREATIVE_DEFAULTS, PARAMETER_RANGES


class TopazCreativeEnhanceNode(BaseTopazNode):
    """Node for creative image enhancement using Topaz Labs generative models."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the Topaz Creative Enhance node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        
        # Generative model selection
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="Creative enhancement model (GAN-based)",
                type=ParameterTypeBuiltin.STR.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["model"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=ENHANCE_GENERATIVE_MODELS)},
                ui_options={"display_name": "Creative Model"}
            )
        )
        
        # Sharpen parameter
        self.add_parameter(
            Parameter(
                name="sharpen",
                tooltip="Sharpen the image (0.0 = no sharpening, 1.0 = maximum sharpening)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["sharpen"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Sharpen",
                    "step": 0.1
                }
            )
        )
        
        # Denoise parameter
        self.add_parameter(
            Parameter(
                name="denoise",
                tooltip="Reduce noise in the image (0.0 = no denoising, 1.0 = maximum denoising)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["denoise"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Denoise",
                    "step": 0.1
                }
            )
        )
        
        # Fix compression parameter
        self.add_parameter(
            Parameter(
                name="fix_compression",
                tooltip="Fix compression artifacts (0.0 = no fix, 1.0 = maximum fix)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["fix_compression"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Fix Compression",
                    "step": 0.1
                }
            )
        )
        
        # Face enhancement toggle
        self.add_parameter(
            Parameter(
                name="face_enhancement",
                tooltip="Enable face enhancement",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["face_enhancement"],
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Face Enhancement"}
            )
        )
        
        # Face enhancement strength
        face_strength_range = PARAMETER_RANGES["face_enhancement_strength"]
        self.add_parameter(
            Parameter(
                name="face_enhancement_strength",
                tooltip="Strength of face enhancement when enabled",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["face_enhancement_strength"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=face_strength_range[0], max_val=face_strength_range[1])},
                ui_options={
                    "display_name": "Face Enhancement Strength",
                    "step": 0.1
                }
            )
        )
    
    def process(self) -> None:
        """Process the image using Topaz Labs creative enhancement."""
        try:
            # Get input image
            image_artifact = self.get_parameter_value("image_input")
            
            # Debug: Check what we got
            if image_artifact is None:
                # Check if there's a connection but no value
                input_param = self.get_parameter_by_name("image_input")
                if input_param and hasattr(input_param, 'connections'):
                    pass  # Could add debug logging here
                raise ValueError("No input image provided")
            
            if not image_artifact:
                raise ValueError("Input image is empty or falsy")
            
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
                "output_format": output_format,
                "sharpen": sharpen,
                "denoise": denoise,
                "fix_compression": fix_compression,
                "face_enhancement": face_enhancement,
                "face_enhancement_strength": face_enhancement_strength
            }
            
            # Create API client and make request
            with self._get_topaz_client() as client:
                processed_image_data = client.enhance(
                    image_data=image_data,
                    **api_params
                )
            
            # Save output image
            output_artifact = self._save_image_output(
                processed_image_data, 
                f"creative_enhanced_{model.lower().replace(' ', '_')}"
            )
            
            # Set output value
            self.parameter_output_values["image_output"] = output_artifact
            
        except Exception as e:
            raise RuntimeError(f"Creative enhancement failed: {str(e)}")
    
    def validate_node(self) -> list[Exception] | None:
        """Validate that required configuration is available."""
        errors = []
        
        # Check API key
        try:
            self._get_api_key()
        except Exception as e:
            errors.append(e)
        
        return errors if errors else None 