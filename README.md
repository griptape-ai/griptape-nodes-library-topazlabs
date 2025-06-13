# Topaz Labs Image Enhancement Nodes for Griptape

Professional image enhancement and denoising nodes powered by the Topaz Labs API. Transform your images with industry-leading AI algorithms for noise reduction, sharpening, facial detail restoration, and creative AI-powered enhancement.

![Topaz Labs](https://img.shields.io/badge/Topaz%20Labs-API-blue)
![Griptape Nodes](https://img.shields.io/badge/Griptape-Nodes-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

## 🚀 Quick Start

### Prerequisites

1. **Topaz Labs API Key** - Get your API key from [Topaz Labs](https://www.topazlabs.com/)
2. **Griptape Nodes** - Running instance of Griptape Nodes

### Installation

1. Clone this repository to your Griptape Nodes workspace
2. Set your API key as an environment variable:
   ```bash
   export TOPAZ_LABS_API_KEY="your_api_key_here"
   ```
3. The nodes will automatically appear in the "Image Processing" category

## 🎯 Available Nodes

### Topaz Denoise
Professional noise reduction with advanced detail preservation algorithms.

### Topaz Enhance  
Comprehensive image enhancement with sharpening, compression fixing, and facial restoration.

### Topaz Creative Enhance ✨ NEW
AI-powered creative enhancement using generative models with prompt-based control for artistic effects.

---

## 📚 Node Reference

## Topaz Denoise Node

Reduces image noise using Topaz Labs' advanced denoising algorithms. Perfect for cleaning up photos taken in low light, high ISO settings, or scanned images.

### Parameters

#### **Model** 
*Dropdown Selection*
- **Normal**: Light noise reduction for subtly noisy images
- **Strong**: Moderate noise reduction for moderately noisy images  
- **Extreme**: Heavy noise reduction for severely noisy images

*Recommendation: Start with Normal and increase if needed*

#### **Strength** 
*Slider: 0.01 - 1.0, Default: 0.5*

Controls how aggressively noise is removed. Higher values remove more noise but may also remove fine details.

- **0.1-0.3**: Subtle noise reduction, preserves maximum detail
- **0.4-0.6**: Balanced noise reduction (recommended starting point)
- **0.7-1.0**: Aggressive noise reduction for heavily degraded images

#### **Minor Deblur**
*Slider: 0.01 - 1.0, Default: 0.1*

Applies mild sharpening after noise reduction to restore sharpness lost during the denoising process.

- **0.0-0.2**: Minimal sharpening restoration
- **0.3-0.5**: Moderate sharpening restoration
- **0.6-1.0**: Strong sharpening restoration

#### **Original Detail**
*Slider: 0.0 - 1.0, Default: 0.5*

Restores fine texture and detail that may be lost during aggressive denoising.

- **0.0-0.3**: Prioritizes smooth noise removal
- **0.4-0.7**: Balanced detail preservation (recommended)
- **0.8-1.0**: Maximum detail preservation (may retain some noise)

#### **Output Format**
*Dropdown: jpeg, png, webp*

Choose the output image format. JPEG for smaller files, PNG for lossless quality.

---

## Topaz Enhance Node

Enhances image sharpness, clarity, and restores facial details using Topaz Labs' enhancement algorithms. Ideal for improving overall image quality and bringing out fine details.

### Parameters

#### **Model**
*Dropdown Selection*
- **Standard V2**: Balanced enhancement for most images
- **Low Resolution V2**: Optimized for web images and low-resolution sources
- **CGI**: Tailored for illustrations and synthetic graphics
- **High Fidelity V2**: Preserves intricate photographic detail
- **Text Refine**: Optimized for documents or text-heavy images

#### **Sharpen**
*Slider: 0.0 - 1.0, Default: 0.0*

Optional additional sharpening beyond the model's default enhancement.

- **0.0**: No additional sharpening (recommended starting point)
- **0.1-0.3**: Subtle additional sharpening
- **0.4-0.7**: Moderate additional sharpening
- **0.8-1.0**: Strong additional sharpening

#### **Denoise**
*Slider: 0.0 - 1.0, Default: 0.0*

Optional denoising during the enhancement process.

- **0.0**: No denoising
- **0.1-0.4**: Light denoising for slightly noisy images
- **0.5-0.8**: Moderate denoising for moderately noisy images
- **0.9-1.0**: Heavy denoising for very noisy images

#### **Fix Compression**
*Slider: 0.0 - 1.0, Default: 0.0*

Repairs artifacts from lossy JPEG compression.

- **0.0**: No compression fixing
- **0.2-0.4**: Light compression artifact removal
- **0.5-0.7**: Moderate compression artifact removal
- **0.8-1.0**: Aggressive compression artifact removal

#### **Face Enhancement**
*Toggle: Default: False*

Enables specialized facial detail restoration algorithms.

#### **Face Enhancement Strength**
*Slider: 0.0 - 1.0, Default: 0.5*

Controls the intensity of facial enhancement (only active when Face Enhancement is enabled).

- **0.1-0.3**: Subtle facial enhancement
- **0.4-0.7**: Moderate facial enhancement (recommended)
- **0.8-1.0**: Strong facial enhancement

#### **Output Format**
*Dropdown: jpeg, png, webp*

Choose the output image format.

---

## Topaz Creative Enhance Node ✨

AI-powered creative enhancement using generative models. Transform your images with artistic effects, intelligent prompting, and creative interpretation while maintaining photographic quality.

### Parameters

#### **Model**
*Dropdown Selection*
- **Redefine**: Balanced creative enhancement with artistic interpretation
- **Recovery**: Specialized for restoring damaged or degraded images creatively
- **Recovery V2**: Advanced version with improved quality and detail preservation

#### **Prompt**
*Text Area*

Text prompt to guide the creative enhancement. Describe the desired artistic effect, mood, or style.

- **Examples**: "cinematic lighting", "vintage film look", "dramatic shadows", "warm golden hour"
- **Leave empty** to use autoprompt (AI analyzes image and generates appropriate enhancement)

#### **Autoprompt**
*Toggle: Default: True*

Let the AI automatically generate a prompt based on image content analysis.

- **True**: AI analyzes image and creates contextual enhancement
- **False**: Use your custom prompt for directed creative enhancement

#### **Creativity**
*Slider: 1 - 6, Default: 3*

Level of creative interpretation and artistic liberty.

- **1-2**: Conservative enhancement, maintains original character
- **3-4**: Balanced creativity with noticeable improvements (recommended)
- **5-6**: High creativity, dramatic artistic transformation

#### **Texture**
*Slider: 1 - 5, Default: 3*

Level of texture enhancement and detail amplification.

- **1-2**: Subtle texture enhancement
- **3**: Balanced texture improvement (recommended)
- **4-5**: Strong texture emphasis, rich detail

#### **Focus Boost**
*Slider: 0.25 - 1.0, Default: 0.5*

Boost focus and sharpness in key areas identified by AI.

- **0.25-0.5**: Gentle focus enhancement
- **0.5-0.75**: Moderate focus boost (recommended)
- **0.75-1.0**: Strong focus enhancement

#### **Seed**
*Number Input: 0 - 999999, Optional*

Random seed for reproducible results. Leave empty for random generation.

- **Use specific seed**: Get consistent results across multiple runs
- **Leave empty**: Generate unique variations each time

#### **Output Format**
*Dropdown: jpeg, png, webp*

Choose the output image format.

---

## 🧑‍🍳 Recipe Guide

### Recipe 1: Enhance an Old Photo

**Goal**: Restore an old, faded photograph with noise and compression artifacts.

**Workflow**:
1. **Topaz Denoise** → **Topaz Enhance**

**Denoise Settings**:
- Model: `Strong` or `Extreme`
- Strength: `0.6-0.8`
- Minor Deblur: `0.3-0.5`
- Original Detail: `0.6-0.8`

**Enhance Settings**:
- Model: `High Fidelity V2`
- Fix Compression: `0.5-0.7`
- Face Enhancement: `True` (if faces present)
- Face Enhancement Strength: `0.6-0.8`

### Recipe 2: Clean Up a Low-Light Photo

**Goal**: Remove noise from a photo taken in low light conditions.

**Workflow**:
1. **Topaz Denoise** only

**Settings**:
- Model: `Normal` or `Strong`
- Strength: `0.4-0.6`
- Minor Deblur: `0.2-0.4`
- Original Detail: `0.7-0.9`

### Recipe 3: Enhance a Web Image

**Goal**: Improve a low-resolution image downloaded from the web.

**Workflow**:
1. **Topaz Enhance** only

**Settings**:
- Model: `Low Resolution V2`
- Sharpen: `0.2-0.4`
- Fix Compression: `0.4-0.6`
- Face Enhancement: `True` (if faces present)

### Recipe 4: Professional Portrait Touch-Up

**Goal**: Enhance a portrait with focus on facial details.

**Workflow**:
1. **Topaz Enhance** only

**Settings**:
- Model: `Standard V2`
- Sharpen: `0.1-0.3`
- Denoise: `0.1-0.3`
- Face Enhancement: `True`
- Face Enhancement Strength: `0.5-0.7`

### Recipe 5: Restore a Heavily Compressed Image

**Goal**: Fix an image with severe JPEG compression artifacts.

**Workflow**:
1. **Topaz Enhance** only

**Settings**:
- Model: `Standard V2` or `High Fidelity V2`
- Fix Compression: `0.7-0.9`
- Sharpen: `0.2-0.4`

### Recipe 6: Maximum Quality Restoration

**Goal**: Apply comprehensive restoration to a damaged image.

**Workflow**:
1. **Topaz Denoise** → **Topaz Enhance**

**Denoise Settings**:
- Model: `Strong`
- Strength: `0.7`
- Minor Deblur: `0.4`
- Original Detail: `0.8`

**Enhance Settings**:
- Model: `High Fidelity V2`
- Sharpen: `0.3`
- Fix Compression: `0.6`
- Face Enhancement: `True`
- Face Enhancement Strength: `0.7`

### Recipe 7: Creative Cinematic Enhancement ✨ NEW

**Goal**: Transform a photo with cinematic, film-like qualities.

**Workflow**:
1. **Topaz Creative Enhance** only

**Settings**:
- Model: `Redefine`
- Prompt: `"cinematic lighting, film grain, dramatic shadows, warm color grading"`
- Autoprompt: `False`
- Creativity: `4-5`
- Texture: `3-4`
- Focus Boost: `0.6-0.8`

### Recipe 8: Artistic Photo Transformation ✨ NEW

**Goal**: Create an artistic interpretation of a photograph.

**Workflow**:
1. **Topaz Creative Enhance** only

**Settings**:
- Model: `Redefine`
- Autoprompt: `True`
- Creativity: `5-6`
- Texture: `4-5`
- Focus Boost: `0.5-0.7`

### Recipe 9: Vintage Photo Revival ✨ NEW

**Goal**: Give modern photos a vintage, nostalgic look.

**Workflow**:
1. **Topaz Creative Enhance** only

**Settings**:
- Model: `Recovery V2`
- Prompt: `"vintage film photography, warm tones, soft lighting, nostalgic mood"`
- Autoprompt: `False`
- Creativity: `3-4`
- Texture: `2-3`
- Focus Boost: `0.4-0.6`

### Recipe 10: Ultimate Creative Restoration ✨ NEW

**Goal**: Comprehensive restoration with creative enhancement.

**Workflow**:
1. **Topaz Denoise** → **Topaz Creative Enhance**

**Denoise Settings**:
- Model: `Strong`
- Strength: `0.6`
- Minor Deblur: `0.3`
- Original Detail: `0.7`

**Creative Enhance Settings**:
- Model: `Recovery V2`
- Autoprompt: `True`
- Creativity: `4`
- Texture: `4`
- Focus Boost: `0.6`

---

## 💡 Tips & Best Practices

### Model Selection Guide

**When to use each Denoise model**:
- **Normal**: Digital camera noise, mild ISO noise
- **Strong**: Scan artifacts, moderate noise from older cameras
- **Extreme**: Heavy film grain, severe digital noise, very old photos

**When to use each Enhance model**:
- **Standard V2**: Most photographs, general enhancement
- **Low Resolution V2**: Social media images, web graphics, thumbnails
- **CGI**: Digital art, 3D renders, illustrations
- **High Fidelity V2**: Professional photography, detailed texture preservation
- **Text Refine**: Screenshots, documents, images with text

**When to use each Creative Enhance model** ✨:
- **Redefine**: Artistic enhancement, creative interpretation, modern photos
- **Recovery**: Damaged photo restoration with creative elements
- **Recovery V2**: Advanced restoration with maximum quality and creative enhancement

### Parameter Tuning Tips

1. **Start Conservative**: Begin with lower values and increase gradually
2. **Preview Effects**: Use the status messages to track processing parameters
3. **Chain Thoughtfully**: Denoise first, then enhance for best results
4. **Face Priority**: Enable face enhancement for portraits and group photos
5. **Format Choice**: Use PNG for archival quality, JPEG for smaller files
6. **Creative Balance**: Higher creativity = more dramatic changes, use sparingly
7. **Prompt Crafting**: Be specific but concise in creative prompts
8. **Seed Consistency**: Use seeds for reproducible creative results

### Workflow Optimization

- **Single Pass**: For light enhancement, use Enhance alone
- **Two Pass**: For heavily degraded images, use Denoise → Enhance
- **Creative Pass**: For artistic effects, use Creative Enhance alone or after cleanup
- **Three Pass Ultimate**: Denoise → Enhance → Creative Enhance for maximum quality
- **Batch Processing**: Connect multiple images to process sets efficiently
- **Quality Check**: Monitor the hash values in status to ensure different images are processed

---

## 🔧 Troubleshooting

### Common Issues

**"No input image provided"**
- Ensure an image is connected to the input
- Check that the image artifact is valid
- Verify the connection is properly established

**"API key not found"**
- Set the `TOPAZ_LABS_API_KEY` environment variable
- Restart Griptape Nodes after setting the environment variable
- Verify the API key is valid and active

**"Request timed out"**
- Large images may take longer to process
- Creative models take longer than standard models
- Check your internet connection
- Verify Topaz Labs API service status

**"Authentication failed"**
- Check your API key is correct
- Verify your Topaz Labs account is active
- Ensure you have sufficient API credits

**Creative Enhancement Issues**:
- Empty prompts with autoprompt disabled may cause errors
- Very high creativity settings may produce unexpected results
- Generative models consume more API credits

### Debug Information

All nodes provide detailed status information:
- Image type and identifier
- Image size in bytes
- Processing hash (to verify different images)
- Current processing stage
- Success/error messages

Use this information to track processing and identify issues.

---

## 📋 API Limits & Considerations

- **File Size**: Images are processed as uploaded, larger files take longer
- **Rate Limits**: Respect Topaz Labs API rate limiting
- **Credits**: Processing consumes API credits based on image size and complexity
- **Timeout**: Large images may timeout after 5 minutes
- **Formats**: Supports common formats (JPEG, PNG, WebP)
- **Generative Models**: Creative enhance models consume more credits and processing time

---

## 🤝 Support

For issues specific to these Griptape nodes:
- Check the troubleshooting section above
- Review the debug information in node status messages
- Verify your API key and network connectivity

For Topaz Labs API issues:
- Visit [Topaz Labs Support](https://www.topazlabs.com/support)
- Check your account status and API credits

For Griptape Nodes platform issues:
- Visit [Griptape Nodes Documentation](https://www.griptapenodes.com/)

---

## 📄 License

This node library is provided as-is for use with Griptape Nodes and the Topaz Labs API. Please ensure you comply with Topaz Labs' terms of service when using their API.
