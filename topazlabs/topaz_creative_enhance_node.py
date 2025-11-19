"""Node for Topaz Labs creative enhancement operations."""

from typing import Dict, Any, Optional
from griptape.artifacts import ImageArtifact
from griptape_nodes.exe_types.node_types import DataNode, BaseNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from base_topaz_node import BaseTopazNode


class TopazCreativeEnhanceNode(BaseTopazNode):
    """Node for creative image enhancement using Topaz Labs Enhance Generative models."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the Topaz Creative Enhance node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        
        # Available Enhance models that work well for creative enhancement
        
        # Model selection
        self.add_parameter(
            Parameter(
                name="model",
                tooltip="Generative enhancement model to use: Redefine for creative changes, Recovery for restoring details.",
                type=ParameterTypeBuiltin.STR.value,
                default_value="Redefine",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=["Redefine", "Recovery", "Recovery V2"])},
                ui_options={"display_name": "Model"}
            )
        )
        
        # Prompt parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="prompt",
                tooltip="A description of the resulting image (max 1024 characters). Use descriptive statements rather than directives.",
                type=ParameterTypeBuiltin.STR.value,
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Prompt",
                    "multiline": True,
                    "placeholder_text": "e.g., girl with red hair and blue eyes"
                }
            )
        )
        
        # Auto-prompt parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="autoprompt",
                tooltip="Use auto-prompting model to generate a prompt. If enabled, ignores manual prompt input.",
                type=ParameterTypeBuiltin.BOOL.value,
                default_value=False,
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={"display_name": "Auto Prompt"}
            )
        )
        
        # Creativity parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="creativity",
                tooltip="Lower values maintain highest fidelity. Higher values provide more creative results (1-6).",
                type=ParameterTypeBuiltin.INT.value,
                default_value=3,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=1, max_val=6)},
                ui_options={
                    "display_name": "Creativity",
                    "step": 1
                }
            )
        )
        
        # Texture parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="texture",
                tooltip="Add texture to the image. Recommend 1 for low creativity, 3 for higher creativity (1-5).",
                type=ParameterTypeBuiltin.INT.value,
                default_value=1,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=1, max_val=5)},
                ui_options={
                    "display_name": "Texture",
                    "step": 1
                }
            )
        )
        
        # Sharpen parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="sharpen",
                tooltip="Slightly sharpens the image (0.0-1.0)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Sharpen",
                    "step": 0.1
                }
            )
        )
        
        # Denoise parameter (Redefine only)
        self.add_parameter(
            Parameter(
                name="denoise",
                tooltip="Reduces noise in the image (0.0-1.0)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.0,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Denoise",
                    "step": 0.1
                }
            )
        )
        
        # Detail parameter (Recovery models only)
        self.add_parameter(
            Parameter(
                name="detail",
                tooltip="Adjusts the level of added detail after rendering (0.0-1.0)",
                type=ParameterTypeBuiltin.FLOAT.value,
                default_value=0.5,
                allowed_modes={ParameterMode.PROPERTY},
                traits={Slider(min_val=0.0, max_val=1.0)},
                ui_options={
                    "display_name": "Detail",
                    "step": 0.1
                }
            )
        )
        
        # Add output parameters in the correct order
        self._add_output_parameters()
    
    async def _process_async(self) -> None:
        """Process the image using Topaz Labs Enhance Generative models."""
        try:
            # Get input image
            image_artifact = self.get_parameter_value("image_input")
            
            if image_artifact is None:
                raise ValueError("No input image provided")
            
            if not image_artifact:
                raise ValueError("Input image is empty or falsy")
            
            # Extract image data
            image_data = self._get_image_data(image_artifact)
            
            # Get model selection
            model = self.get_parameter_value("model")
            output_format = self.get_parameter_value("output_format")
            
            # Prepare API parameters based on model
            api_params = {
                "model": model,
                "output_format": output_format
            }
            
            # Add model-specific parameters as additionalProperties
            if model == "Redefine":
                # Redefine model parameters
                prompt = self.get_parameter_value("prompt")
                autoprompt = self.get_parameter_value("autoprompt")
                creativity = self.get_parameter_value("creativity")
                texture = self.get_parameter_value("texture")
                sharpen = self.get_parameter_value("sharpen")
                denoise = self.get_parameter_value("denoise")
                
                # Only include prompt if autoprompt is disabled and prompt is provided
                if not autoprompt and prompt and prompt.strip():
                    api_params["prompt"] = prompt.strip()
                
                # Fix parameter types - handle cases where parameters return unexpected types
                if not isinstance(sharpen, (int, float)):
                    sharpen = 0.0  # Use default value if parameter returns wrong type
                if not isinstance(denoise, (int, float)):
                    denoise = 0.0  # Use default value if parameter returns wrong type
                
                # Debug: Check what we're getting from parameters
                print(f"DEBUG NODE: Raw parameter values:")
                print(f"  autoprompt={autoprompt} ({type(autoprompt)})")
                print(f"  creativity={creativity} ({type(creativity)})")
                print(f"  texture={texture} ({type(texture)})")
                print(f"  sharpen={sharpen} ({type(sharpen)})")
                print(f"  denoise={denoise} ({type(denoise)})")
                
                # Add all Redefine parameters as documented
                # Convert boolean to the string format the API expects
                api_params["autoprompt"] = "true" if autoprompt else "false"
                api_params["creativity"] = int(creativity)
                api_params["texture"] = int(texture)
                api_params["sharpen"] = float(sharpen)
                api_params["denoise"] = float(denoise)
                
                print(f"DEBUG NODE: Converted parameter values:")
                print(f"  autoprompt={api_params['autoprompt']} ({type(api_params['autoprompt'])})")
                print(f"  creativity={api_params['creativity']} ({type(api_params['creativity'])})")
                print(f"  texture={api_params['texture']} ({type(api_params['texture'])})")
                print(f"  sharpen={api_params['sharpen']} ({type(api_params['sharpen'])})")
                print(f"  denoise={api_params['denoise']} ({type(api_params['denoise'])})")
                
            elif model in ["Recovery", "Recovery V2"]:
                # Recovery model parameters
                detail = self.get_parameter_value("detail")
                if detail is not None:
                    api_params["detail"] = detail
            
            # Create API client and make request
            print(f"DEBUG: About to call client.enhance_gen with api_params: {api_params}")
            with self._get_topaz_client() as client:
                processed_image_data = client.enhance_gen(
                    image_data=image_data,
                    **api_params
                )
            
            # Save output image
            output_artifact = self._save_image_output(
                processed_image_data, 
                f"enhance_generative_{model.lower().replace(' ', '_')}"
            )
            
            # Set output value
            self.parameter_output_values["image_output"] = output_artifact
            
        except Exception as e:
            raise RuntimeError(f"Enhance Generative processing failed: {str(e)}")
    
    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate that required configuration is available before execution."""
        errors = []
        
        # Check API key
        try:
            self._get_api_key()
        except Exception as e:
            errors.append(e)
        
        return errors if errors else None
    
    def validate_before_workflow_run(self) -> list[Exception] | None:
        return self.validate_before_node_run() 