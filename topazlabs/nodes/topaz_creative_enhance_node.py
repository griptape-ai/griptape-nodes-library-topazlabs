"""Topaz Labs Creative Enhancement Node for Griptape."""

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
from utils.constants import ENHANCE_GENERATIVE_MODELS, ENHANCE_CREATIVE_DEFAULTS, PARAMETER_RANGES


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
                tooltip="Generative model for creative enhancement",
                type=ParameterTypeBuiltin.STR.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["model"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=ENHANCE_GENERATIVE_MODELS)},
                ui_options={"display_name": "Creative Model"}
            )
        )
        
        # Prompt for creative direction
        self.add_parameter(
            Parameter(
                name="prompt",
                tooltip="Text prompt to guide the creative enhancement (leave empty to use autoprompt)",
                type=ParameterTypeBuiltin.STR.value, 
                default_value=ENHANCE_CREATIVE_DEFAULTS["prompt"],
                allowed_modes={ParameterMode.PROPERTY, ParameterMode.INPUT},
                ui_options={
                    "display_name": "Creative Prompt",
                    "multiline": True
                }
            )
        )
        
        # Autoprompt toggle
        self.add_parameter(
            Parameter(
                name="autoprompt",
                tooltip="Let the AI automatically generate a prompt based on image content",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["autoprompt"],
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Auto Prompt"}
            )
        )
        
        # Creativity level
        creativity_range = PARAMETER_RANGES["creativity"]
        self.add_parameter(
            Parameter(
                name="creativity",
                tooltip="Level of creative interpretation (1=conservative, 6=highly creative)",
                type=ParameterTypeBuiltin.INT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["creativity"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=creativity_range[0], max_val=creativity_range[1])},
                ui_options={
                    "display_name": "Creativity Level",
                    "step": 1
                }
            )
        )
        
        # Texture enhancement
        texture_range = PARAMETER_RANGES["texture"]
        self.add_parameter(
            Parameter(
                name="texture",
                tooltip="Level of texture enhancement (1=minimal, 5=maximum)",
                type=ParameterTypeBuiltin.INT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["texture"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=texture_range[0], max_val=texture_range[1])},
                ui_options={
                    "display_name": "Texture Enhancement",
                    "step": 1
                }
            )
        )
        
        # Random seed for reproducibility
        self.add_parameter(
            Parameter(
                name="seed",
                tooltip="Random seed for reproducible results (leave empty for random)",
                type=ParameterTypeBuiltin.INT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["seed"],
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Seed"}
            )
        )
        
        # Focus boost
        focus_range = PARAMETER_RANGES["focus_boost"]
        self.add_parameter(
            Parameter(
                name="focus_boost",
                tooltip="Boost focus and sharpness in key areas",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=ENHANCE_CREATIVE_DEFAULTS["focus_boost"],
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=focus_range[0], max_val=focus_range[1])},
                ui_options={
                    "display_name": "Focus Boost",
                    "step": 0.05
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
            prompt = self.get_parameter_value("prompt")
            autoprompt = self.get_parameter_value("autoprompt")
            creativity = self.get_parameter_value("creativity")
            texture = self.get_parameter_value("texture")
            seed = self.get_parameter_value("seed")
            focus_boost = self.get_parameter_value("focus_boost")
            output_format = self.get_parameter_value("output_format")
            
            # Prepare API parameters
            api_params = {
                "model": model,
                "output_format": output_format,
                "autoprompt": autoprompt,
                "creativity": creativity,
                "texture": texture,
                "focus_boost": focus_boost
            }
            
            # Add prompt if provided and autoprompt is disabled
            if not autoprompt and prompt and prompt.strip():
                api_params["prompt"] = prompt.strip()
            
            # Add seed if provided
            if seed is not None:
                api_params["seed"] = seed
            
            # Create API client and make request
            with self._get_topaz_client() as client:
                processed_image_data = client.enhance_gen(
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