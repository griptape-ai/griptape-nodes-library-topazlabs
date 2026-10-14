"""Base node for Topaz Labs operations."""

import asyncio
import hashlib
from typing import Any

from constants import API_KEY_ENV_VAR, OUTPUT_FORMATS
from griptape.artifacts import ImageUrlArtifact
from griptape_nodes.exe_types.core_types import NodeError, Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.exe_types.node_types import AsyncResult, ControlNode
from griptape_nodes.exe_types.param_components.project_file_parameter import ProjectFileParameter
from griptape_nodes.files.file import File
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from griptape_nodes.traits.options import Options
from topaz_client import TopazClient
from topaz_errors import empty_input_error, missing_api_key_error, missing_input_error, unreadable_input_error


class BaseTopazNode(ControlNode):
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
                ui_options={"display_name": "Input Image"},
            )
        )

        # Output format selection (configuration parameter)
        self.add_parameter(
            Parameter(
                name="output_format",
                tooltip="Output image format",
                type=ParameterTypeBuiltin.STR.value,
                default_value="jpeg",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                traits={Options(choices=OUTPUT_FORMATS)},
                ui_options={"display_name": "Output Format"},
            )
        )

    def _add_output_parameters(self) -> None:
        """Add output parameters after configuration parameters.

        This method should be called by subclasses after they add their
        configuration parameters to ensure proper parameter ordering:
        1. Input parameters
        2. Configuration parameters
        3. Output parameters
        4. Status parameter
        """
        # File destination parameter for configuring where output is saved
        self._output_file = ProjectFileParameter(
            node=self,
            name="output_file",
            default_filename="processed_image.jpeg",
        )
        self._output_file.add_parameter()

        # Common output parameter for processed image
        self.add_parameter(
            Parameter(
                name="image_output",
                tooltip="Processed image output",
                type="ImageArtifact",
                output_type="ImageArtifact",
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={"display_name": "Output Image", "pulse_on_run": True},
            )
        )

        # Status message for user feedback (always last)
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
                    "placeholder_text": "Status messages",
                },
            )
        )

    def _get_api_key(self) -> str:
        """Retrieve the API key from configuration.

        Returns:
            The Topaz Labs API key

        Raises:
            NodeError: If API key is not found
        """
        api_key = GriptapeNodes.SecretsManager().get_secret(API_KEY_ENV_VAR)
        if not api_key:
            raise missing_api_key_error()
        return api_key

    def _get_topaz_client(self) -> TopazClient:
        """Create and return a Topaz Labs API client.

        Returns:
            Configured TopazClient instance

        Raises:
            NodeError: If API key is not available
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
            NodeError: If the image is missing, unreadable or empty
        """
        if not image_artifact:
            raise missing_input_error("Input Image", "image")

        try:
            if isinstance(image_artifact, ImageUrlArtifact):
                # Use File to resolve template paths like {outputs}/... to real file paths
                image_bytes = File(image_artifact.value).read_bytes()
            else:
                image_bytes = image_artifact.to_bytes()
        except Exception as e:
            raise unreadable_input_error("Input Image", "image", e) from e

        # Verify we have image data
        if not image_bytes or len(image_bytes) < 100:
            raise empty_input_error("Input Image", "image")

        # Create hash to track if image changed
        image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
        image_size = len(image_bytes)

        if hasattr(image_artifact, "value"):
            image_id = (
                str(image_artifact.value)[:30] + "..."
                if len(str(image_artifact.value)) > 30
                else str(image_artifact.value)
            )
        else:
            image_id = f"hash_{image_hash}"

        self._update_status(f"Processing: {image_id} ({image_size} bytes, hash: {image_hash})", show=True)

        return image_bytes

    def _save_image_output(self, image_data: bytes, filename_hint: str = "processed_image") -> ImageUrlArtifact:
        """Save processed image data and create output artifact.

        Args:
            image_data: Binary image data
            filename_hint: Hint for the filename

        Returns:
            ImageUrlArtifact pointing to the saved image

        """
        dest = self._output_file.build_file()
        saved = dest.write_bytes(image_data)
        return ImageUrlArtifact(value=saved.location, name=filename_hint)

    def _update_status(self, message: str, show: bool = True) -> None:
        """Update the status parameter with a message.

        Args:
            message: Status message to display
            show: Whether to show the status parameter in UI
        """
        self.set_parameter_value("status", message)
        status_param = self.get_parameter_by_name("status")
        if status_param and hasattr(status_param, "_ui_options"):
            status_param._ui_options["hide"] = not show

    def _api_key_errors(self) -> list[Exception] | None:
        """Return an error for a missing API key, or None when it is set."""
        try:
            self._get_api_key()
        except NodeError as e:
            return [e]
        return None

    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate the node configuration before execution.

        Returns:
            List of validation errors, or None if valid
        """
        return self._api_key_errors()

    def validate_before_workflow_run(self) -> list[Exception] | None:
        """Check only the API key before the workflow starts; inputs are checked when the node runs."""
        return self._api_key_errors()

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
