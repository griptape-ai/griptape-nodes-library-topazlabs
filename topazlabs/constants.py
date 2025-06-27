"""Constants for Topaz Labs API integration."""

# Service configuration
SERVICE = "TOPAZ_LABS"
API_KEY_ENV_VAR = "TOPAZ_LABS_API_KEY"
API_BASE_URL = "https://api.topazlabs.com/image/v1"
VIDEO_API_BASE_URL = "https://api.topazlabs.com/video"

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

# Generative enhance models (per OpenAPI spec)
ENHANCE_GENERATIVE_MODELS = [
    "Recovery",
    "Recovery V2", 
    "Redefine"
]

# Creative enhance models (alias for generative models)
CREATIVE_ENHANCE_MODELS = ENHANCE_GENERATIVE_MODELS

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

# Creative enhancement defaults for generative models - Updated for GAN models
ENHANCE_CREATIVE_DEFAULTS = {
    "model": "High Fidelity V2",
    "sharpen": 0.0,
    "denoise": 0.0,
    "fix_compression": 0.0,
    "face_enhancement": True,
    "face_enhancement_strength": 0.7
}

# Creative enhance defaults (alias for consistency)
CREATIVE_ENHANCE_DEFAULTS = ENHANCE_CREATIVE_DEFAULTS

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

# Video API Constants
VIDEO_MODELS = {
    # Upscaling & Detail Enhancement
    "aaa-9": "High-quality upscaling with detail enhancement",
    "ahq-12": "Archival quality upscaling",
    "alq-13": "Low-quality input optimization",
    "alqs-2": "Low-quality specialized processing",
    "amq-13": "Medium-quality enhancement",
    "amqs-2": "Medium-quality specialized processing",
    "apf-2": "Professional film enhancement",
    
    # Denoising & Compression Recovery
    "chf-3": "Compression artifact removal",
    "chr-2": "Compression recovery",
    "ddv-3": "Digital video denoising",
    "dtd-4": "Digital temporal denoising",
    "dtds-2": "Digital temporal denoising specialized",
    "dtv-4": "Digital temporal video processing",
    "dtvs-2": "Digital temporal video specialized",
    
    # Frame Interpolation & Motion Enhancement
    "gcg-5": "General content generation",
    "ghq-5": "High-quality generation",
    "iris-2": "Intelligent resolution improvement",
    "iris-3": "Advanced resolution improvement",
    "nxf-1": "Next-gen frame processing",
    "nyx-3": "Advanced motion processing",
    
    # Sharpening & Texture Recovery
    "prob-4": "Professional broadcast quality",
    "rhea-1": "Generative AI upscaling",
    "rxl-1": "Resolution excellence",
    "thd-3": "Texture and detail enhancement",
    "thf-4": "Texture high-fidelity",
    "thm-2": "Texture medium processing",
    
    # Popular presets
    "apo-8": "Frame interpolation (60fps conversion)"
}

VIDEO_CONTAINERS = ["mp4", "mov", "avi"]
VIDEO_CODECS = ["H264", "H265", "ProRes"]
AUDIO_CODECS = ["AAC", "MP3", "PCM"]
AUDIO_TRANSFER_MODES = ["Copy", "Transcode", "Remove"]
VIDEO_PROFILES = ["Baseline", "Main", "High"]
COMPRESSION_LEVELS = ["Low", "Medium", "High"]
AUDIO_BITRATES = ["128", "192", "256", "320"]

# Common frame rates
FRAME_RATES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120]

# Video processing defaults
VIDEO_DEFAULTS = {
    "model": "apo-8",
    "output_fps": 60,
    "slowmo": 1,
    "duplicate": True,
    "duplicate_threshold": 0.1,
    "container": "mp4",
    "video_encoder": "H265",
    "video_profile": "Main",
    "audio_codec": "AAC",
    "audio_transfer": "Copy",
    "audio_bitrate": "320",
    "compression_level": "High",
    "crop_to_fit": False
}

# Video parameter ranges
VIDEO_PARAMETER_RANGES = {
    "slowmo": (1, 8),
    "duplicate_threshold": (0.0, 1.0),
    "compression": (0.0, 1.0),
    "details": (0.0, 1.0),
    "noise": (0.0, 1.0),
    "sharpen": (0.0, 1.0),
    "focus_fix_level": (0.0, 1.0),
    "recover_original_detail_value": (0.0, 1.0)
} 