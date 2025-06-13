"""Constants for Topaz Labs API integration."""

# Service configuration
SERVICE = "TOPAZ_LABS"
API_KEY_ENV_VAR = "TOPAZ_LABS_API_KEY"
API_BASE_URL = "https://api.topazlabs.com/image/v1"

# Output formats
OUTPUT_FORMATS = ["jpeg", "png", "webp"]

# Denoise models
DENOISE_MODELS = [
    "Normal",
    "Strong", 
    "Extreme"
]

# Enhance models - Standard class (fast, high fidelity)
ENHANCE_MODELS = [
    "Standard V2",
    "Low Resolution V2",
    "CGI",
    "High Fidelity V2",
    "Text Refine"
]

# Generative enhance models (slower, creative)
ENHANCE_GENERATIVE_MODELS = [
    "Redefine",
    "Recovery",
    "Recovery V2"
]

# Parameter defaults and ranges
DENOISE_DEFAULTS = {
    "model": "Normal",
    "strength": 0.5,
    "minor_deblur": 0.1,
    "original_detail": 0.5
}

ENHANCE_DEFAULTS = {
    "model": "Standard V2",
    "sharpen": 0.0,
    "denoise": 0.0,
    "fix_compression": 0.0,
    "face_enhancement": False,
    "face_enhancement_strength": 0.5
}

# Creative enhancement defaults for generative models
ENHANCE_CREATIVE_DEFAULTS = {
    "model": "Redefine",
    "prompt": "",
    "autoprompt": True,
    "creativity": 3,
    "texture": 3,
    "seed": None,
    "focus_boost": 0.5
}

# Parameter ranges
PARAMETER_RANGES = {
    "strength": (0.01, 1.0),
    "minor_deblur": (0.01, 1.0),
    "original_detail": (0.0, 1.0),
    "sharpen": (0.0, 1.0),
    "denoise": (0.0, 1.0),
    "fix_compression": (0.0, 1.0),
    "face_enhancement_strength": (0.0, 1.0),
    "creativity": (1, 6),
    "texture": (1, 5),
    "focus_boost": (0.25, 1.0),
    "seed": (0, 999999)
} 