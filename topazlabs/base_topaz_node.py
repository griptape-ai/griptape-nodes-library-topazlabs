"""Base node for Topaz Labs operations."""

from typing import Dict, Any, Optional
from griptape.artifacts import ImageArtifact, ImageUrlArtifact
from griptape_nodes.exe_types.node_types import DataNode, BaseNode
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

from constants import SERVICE, API_KEY_ENV_VAR, OUTPUT_FORMATS
from topaz_client import TopazClient


class BaseTopazNode(DataNode):
    """Base class for all Topaz Labs image processing nodes."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        """Initialize the base Topaz node.
        
        Args:
            name: Node instance name
            metadata: Optional metadata dictionary
        """
        super().__init__(name, metadata)
        # Common input parameter for image
        self.add_parameter(
            Parameter(
                name="image_input",
                tooltip="Input image to process",
                type="ImageArtifact",
                input_types=["ImageArtifact", "ImageUrlArtifact"],
                allowed_modes={ParameterMode.INPUT},
                ui_options={"display_name": "Input Image"}
            )
        )
        
        # Output format selection
        self.add_parameter(
            Parameter(
                name="output_format",
                tooltip="Output image format",
                type=ParameterTypeBuiltin.STR.value,
                default_value="jpeg",
                allowed_modes={ParameterMode.PROPERTY},
                traits={Options(choices=OUTPUT_FORMATS)},
                ui_options={"display_name": "Output Format"}
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
        
        # Common output parameter for processed image
        self.add_parameter(
            Parameter(
                name="image_output",
                tooltip="Processed image output",
                type="ImageArtifact",
                output_type="ImageArtifact",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "display_name": "Output Image",
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
    
    def _get_image_data(self, image_artifact: Any) -> bytes:
        """Extract image data from artifact.
        
        Args:
            image_artifact: ImageArtifact or ImageUrlArtifact
            
        Returns:
            Image data as bytes
            
        Raises:
            ValueError: If image artifact is invalid or unsupported
        """
        if not image_artifact:
            raise ValueError("No input image provided")
        
        try:
            # Debug info to track image changes - create a hash to detect changes
            import hashlib
            
            if isinstance(image_artifact, (ImageArtifact, ImageUrlArtifact)):
                image_bytes = image_artifact.to_bytes()
            else:
                # Try to convert to bytes if it's a different artifact type
                image_bytes = image_artifact.to_bytes()
            
            # Verify we have image data
            if not image_bytes or len(image_bytes) < 100:
                raise ValueError("Image data is empty or too small")
            
            # Create hash to track if image changed
            image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
            image_size = len(image_bytes)
            
            # Debug info to track image changes
            if hasattr(image_artifact, 'value'):
                image_id = str(image_artifact.value)[:30] + "..." if len(str(image_artifact.value)) > 30 else str(image_artifact.value)
            else:
                image_id = f"hash_{image_hash}"
            
            self._update_status(f"Processing: {image_id} ({image_size} bytes, hash: {image_hash})", show=True)
            
            return image_bytes
            
        except Exception as e:
            raise ValueError(f"Failed to extract image data: {str(e)}")
    
    def _save_image_output(self, image_data: bytes, filename_hint: str = "processed_image") -> ImageUrlArtifact:
        """Save processed image data and create output artifact.
        
        Args:
            image_data: Binary image data
            filename_hint: Hint for the filename
            
        Returns:
            ImageUrlArtifact pointing to the saved image
            
        Raises:
            Exception: If saving fails
        """
        try:
            # Import inside method to avoid caching issues
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
            
            # Get output format
            output_format = self.get_parameter_value("output_format") or "jpeg"
            
            # Generate unique filename with timestamp and hash (following kontext pattern)
            import hashlib
            import time
            
            timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
            content_hash = hashlib.md5(image_data).hexdigest()[:8]  # Short hash of content
            filename = f"{filename_hint}_{timestamp}_{content_hash}.{output_format.lower()}"
            
            # Save to managed file location and get URL
            static_url = GriptapeNodes.StaticFilesManager().save_static_file(
                image_data, filename
            )
            
            return ImageUrlArtifact(
                value=static_url, name=f"{filename_hint}_{timestamp}"
            )
            
        except Exception as e:
            raise Exception(f"Failed to save output image: {str(e)}")
    
    def _update_status(self, message: str, show: bool = True) -> None:
        """Update the status parameter with a message.
        
        Args:
            message: Status message to display
            show: Whether to show the status parameter in UI
        """
        self.set_parameter_value("status", message)
        status_param = self.get_parameter_by_name("status")
        if status_param and hasattr(status_param, '_ui_options'):
            status_param._ui_options["hide"] = not show
    
    def validate_node(self) -> list[Exception] | None:
        """Validate the node configuration.
        
        Returns:
            List of validation errors, or None if valid
        """
        errors = []
        
        # Check API key
        try:
            self._get_api_key()
        except ValueError as e:
            errors.append(e)
        
        return errors if errors else None
    
    def process(self) -> None:
        """Abstract process method - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the process method") 