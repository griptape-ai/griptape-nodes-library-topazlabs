# Topaz Labs Nodes for Griptape

This library provides Griptape Nodes for interacting with Topaz Labs' AI-powered image enhancement APIs, enabling professional-grade image processing capabilities directly within your Griptape workflows.

## Features

### Image Processing
- **Topaz Denoise**: Remove noise from images while preserving detail and sharpness
- **Topaz Enhance**: Sharpen and enhance image quality with advanced AI upscaling
- **Topaz Creative Enhance**: Apply creative AI enhancement with artistic control and face enhancement

### Video Processing
- **Topaz Frame Interpolation**: Convert videos to 60fps with smooth motion and slow motion effects
- **Topaz Video Upscale**: AI-powered video upscaling with resolution enhancement and quality improvement
- **Topaz Video Denoise**: Remove noise and compression artifacts from videos with temporal consistency

## Installation

1. Clone this repository into your Griptape Nodes workspace directory:

```bash
# Navigate to your workspace directory
cd $(gtn config show | grep workspace_directory | cut -d'"' -f4)

# Clone the repository
git clone https://github.com/griptape-ai/griptape-nodes-library-topazlabs.git
```

2. Install dependencies:

```bash
cd griptape-nodes-library-topazlabs
uv sync
```

## API Key Setup

You'll need a Topaz Labs API key to use these nodes.

### Get Your API Key

1. Visit [Topaz Labs](https://www.topazlabs.com/)
2. Create an account and access their API services
3. Generate a new API key from your account dashboard

### Configure Your API Key

Configure your API key through the Griptape Nodes IDE:

1. Open the **Settings** menu.
2. Navigate to the **API Keys & Secrets** panel.
3. Add a new secret configuration for the service named `Topaz Labs`.
4. Enter your `TOPAZ_LABS_API_KEY` in the respective field.

## Add your library to your installed Engine!

If you haven't already installed your Griptape Nodes engine, follow the installation steps [HERE](https://github.com/griptape-ai/griptape-nodes).
After you've completed those and you have your engine up and running:

1. Copy the path to your `griptape-nodes-library.json` file within this `topazlabs` directory. Right click on the file, and `Copy Path` (Not `Copy Relative Path`).
2. Start up the engine!
3. Navigate to settings.
4. Open your settings and go to the App Events tab. Add an item in **Libraries to Register**.
5. Paste your copied `griptape-nodes-library.json` path from earlier into the new item.
6. Exit out of Settings. It will save automatically!
7. Open up the **Libraries** dropdown on the left sidebar.
8. Your newly registered library should appear! Drag and drop nodes to use them!

## Available Nodes

### Topaz Denoise

Reduces image noise using advanced AI algorithms while preserving fine details and image sharpness.

**Parameters:**
- **Input Image**: Accepts ImageArtifact or ImageUrlArtifact
- **Model**: Choose from:
  - `Normal` (balanced noise reduction, default)
  - `Strong` (aggressive noise reduction)
  - `Extreme` (maximum noise reduction for heavily degraded images)
- **Strength**: Noise reduction intensity (0.01-1.0, default: 0.5)
- **Minor Deblur**: Slight sharpening to counteract softening (0.01-1.0, default: 0.1)
- **Original Detail**: Preserve original image details (0.0-1.0, default: 0.5)
- **Output Format**: JPEG, PNG, or WebP

**Best for:**
- High ISO photography
- Scanned documents or old photos
- Low-light images with noise
- Preparing images for further enhancement

### Topaz Enhance

Enhances image sharpness, clarity, and overall quality using AI upscaling and enhancement algorithms.

**Parameters:**
- **Input Image**: Accepts ImageArtifact or ImageUrlArtifact
- **Model**: Choose from:
  - `Standard V2` (balanced enhancement, default)
  - `Low Resolution V2` (optimized for low-res images)
  - `CGI` (specialized for computer-generated imagery)
  - `High Fidelity V2` (maximum quality preservation)
  - `Text Refine` (optimized for text and line art)
- **Sharpen**: Edge sharpening intensity (0.0-1.0, default: 0.0)
- **Denoise**: Built-in noise reduction (0.0-1.0, default: 0.0)
- **Fix Compression**: Repair JPEG compression artifacts (0.0-1.0, default: 0.0)
- **Face Enhancement**: Enable AI face enhancement (boolean, default: False)
- **Face Enhancement Strength**: Face enhancement intensity (0.0-1.0, default: 0.5)
- **Output Format**: JPEG, PNG, or WebP

**Best for:**
- Upscaling images for print
- Enhancing web images
- Sharpening soft or blurry photos
- Professional photo editing workflows

### Topaz Creative Enhance

Apply creative AI enhancement with advanced artistic control and specialized face enhancement capabilities.

**Parameters:**
- **Input Image**: Accepts ImageArtifact or ImageUrlArtifact
- **Model**: Choose from:
  - `High Fidelity V2` (maximum quality with creative enhancement, default)
  - `CGI` (specialized for computer-generated imagery)
  - `Text Refine` (optimized for text and line art)
- **Sharpen**: Creative sharpening intensity (0.0-1.0, default: 0.0)
- **Denoise**: Intelligent noise reduction (0.0-1.0, default: 0.0)
- **Fix Compression**: Advanced compression artifact repair (0.0-1.0, default: 0.0)
- **Face Enhancement**: AI-powered face enhancement (boolean, default: True)
- **Face Enhancement Strength**: Face enhancement intensity (0.0-1.0, default: 0.7)
- **Output Format**: JPEG, PNG, or WebP

**Best for:**
- Portrait photography enhancement
- Creative photo editing
- Artistic image processing
- Professional headshots and portraits

### Topaz Frame Interpolation

Convert videos to higher frame rates with smooth motion interpolation and slow motion effects.

**Parameters:**
- **Input Video**: Accepts VideoUrlArtifact or BlobArtifact
- **Model**: Choose from:
  - `apo-8` (popular 60fps conversion, default)
  - `gcg-5` (general content generation)
  - `ghq-5` (high-quality generation)
  - `iris-2` / `iris-3` (intelligent resolution improvement)
  - `nxf-1` (next-gen frame processing)
  - `nyx-3` (advanced motion processing)
- **Target FPS**: Output frame rate (23.976 to 120 fps)
- **Slow Motion Factor**: Slow motion multiplier (1-8x)
- **Remove Duplicate Frames**: Intelligent duplicate frame detection
- **Duplicate Threshold**: Detection sensitivity (0.0-1.0)
- **Output Settings**: Container format, codecs, audio handling

**Best for:**
- Converting 30fps to 60fps for smooth playback
- Creating slow motion effects
- Improving motion in low frame rate content
- Gaming and sports video enhancement

### Topaz Video Upscale

Enhance video resolution and quality using AI-powered upscaling with detail recovery.

**Parameters:**
- **Input Video**: Accepts VideoUrlArtifact or BlobArtifact
- **Model**: Choose from:
  - `prob-4` (professional broadcast quality, default)
  - `rhea-1` (generative AI 4x upscaling)
  - `aaa-9` (high-quality with detail enhancement)
  - `ahq-12` (archival quality upscaling)
  - And more specialized models
- **Upscale Factor**: 2x, 4x, or Auto
- **Detail Enhancement**: Fine detail and texture enhancement (0.0-1.0)
- **Sharpening**: Edge sharpening intensity (0.0-1.0)
- **Noise Reduction**: Built-in noise reduction (0.0-1.0)
- **Compression Recovery**: Remove compression artifacts (0.0-1.0)
- **Focus Fix**: Blur and focus correction (0.0-1.0)
- **Original Detail Recovery**: Recover lost details (0.0-1.0)

**Best for:**
- Upscaling low-resolution videos
- Enhancing old or degraded footage
- Preparing content for larger displays
- Archival and restoration projects

### Topaz Video Denoise

Remove noise and compression artifacts from videos while maintaining temporal consistency.

**Parameters:**
- **Input Video**: Accepts VideoUrlArtifact or BlobArtifact
- **Model**: Choose from:
  - `nyx-3` (advanced motion processing with auto denoising, default)
  - `ddv-3` (digital video denoising)
  - `dtd-4` / `dtv-4` (digital temporal denoising)
  - `chf-3` / `chr-2` (compression artifact removal)
- **Auto Mode**: Automatic processing based on content analysis
- **Auto Type**: Relative, Absolute, or Custom processing
- **Noise Intensity**: Manual noise reduction intensity (0.0-1.0)
- **Compression Recovery**: Remove compression artifacts (0.0-1.0)
- **Detail Preservation**: Preserve fine details (0.0-1.0)
- **Temporal Consistency**: Maintain frame-to-frame consistency (0.0-1.0)
- **Sharpening**: Mild sharpening to counteract softening (0.0-1.0)

**Best for:**
- Cleaning up noisy footage from high ISO recordings
- Removing compression artifacts from heavily compressed videos
- Restoring old or damaged video content
- Preprocessing for further video editing

## Model Comparison

### When to Use Each Node

**Use Topaz Denoise for:**
- Noisy images from high ISO settings
- Scanned photos or documents
- Low-light photography
- Preprocessing before other enhancements

**Use Topaz Enhance for:**
- General image sharpening and clarity
- Upscaling for print or display
- Fixing soft or slightly blurry images
- Professional photo workflows

**Use Topaz Creative Enhance for:**
- Portrait photography
- Creative artistic effects
- Face-focused enhancement
- High-end photo retouching

**Use Topaz Frame Interpolation for:**
- Converting videos to 60fps or higher
- Creating smooth slow motion effects
- Improving motion in low frame rate content
- Gaming and sports video enhancement

**Use Topaz Video Upscale for:**
- Upscaling low-resolution videos (2x or 4x)
- Enhancing old or degraded footage
- Preparing content for larger displays
- Archival and restoration projects

**Use Topaz Video Denoise for:**
- Cleaning up noisy footage
- Removing compression artifacts
- Restoring old or damaged video content
- Preprocessing for further video editing

## Example Workflows

### Basic Image Enhancement

1. Add a **Topaz Enhance** node
2. Choose your model (`Standard V2` for general use)
3. Adjust sharpening and denoising as needed
4. Enable face enhancement for portraits
5. Run the workflow
6. The enhanced image will be available as an ImageArtifact output

### Noise Reduction Pipeline

1. **Start with Topaz Denoise**: Remove noise first with appropriate model strength
2. **Follow with Topaz Enhance**: Sharpen and enhance the cleaned image
3. **Fine-tune Parameters**: Adjust settings based on image content and desired output

### Portrait Enhancement Workflow

1. **Optional: Topaz Denoise** for noisy portraits
2. **Topaz Creative Enhance**: Use with face enhancement enabled
3. **Adjust Face Enhancement Strength**: Higher values for more dramatic improvements

### Video Enhancement Pipeline

1. **Start with Topaz Video Denoise**: Clean up noisy or compressed footage
2. **Follow with Topaz Video Upscale**: Enhance resolution and detail
3. **Optional: Topaz Frame Interpolation**: Convert to higher frame rates for smooth motion

### 60fps Conversion Workflow

1. Add a **Topaz Frame Interpolation** node
2. Choose `apo-8` model for reliable 60fps conversion
3. Set target FPS to 60
4. Enable duplicate frame removal
5. Configure output settings (H265 recommended for quality)

### Video Restoration Workflow

1. **Topaz Video Denoise**: Remove noise and compression artifacts first
2. **Topaz Video Upscale**: Enhance resolution and recover details
3. **Fine-tune Parameters**: Adjust based on source material quality

## Advanced Features

### Parameter Optimization

Each node offers precise control over enhancement parameters:

- **Strength/Intensity Controls**: Fine-tune the effect strength for natural results
- **Detail Preservation**: Balance enhancement with original image characteristics  
- **Format Selection**: Choose optimal output format for your use case

### Chaining Nodes

Topaz nodes work excellently in sequence:

**Image Processing Chains:**
1. **Denoise** → **Enhance** → **Creative Enhance** for maximum quality
2. **Enhance** → **Creative Enhance** for portraits
3. **Denoise** → **Enhance** for general cleanup and sharpening

**Video Processing Chains:**
1. **Video Denoise** → **Video Upscale** → **Frame Interpolation** for complete enhancement
2. **Video Denoise** → **Video Upscale** for quality improvement
3. **Frame Interpolation** alone for smooth motion conversion
4. **Video Upscale** alone for resolution enhancement

### Quality vs Speed Trade-offs

**Image Processing:**
- **Normal/Standard models**: Faster processing, good quality
- **Strong/High Fidelity models**: Slower processing, maximum quality
- **Specialized models**: Optimized for specific content types

**Video Processing:**
- **Auto mode**: Faster processing with intelligent parameter selection
- **Manual mode**: Full control but requires parameter tuning
- **Generative models** (like rhea-1): Slower but highest quality upscaling
- **Temporal models**: Better for maintaining consistency across frames

## Output Formats

**Image Output Formats:**
- **JPEG**: Smaller file size, good for web use
- **PNG**: Lossless compression, best for archival
- **WebP**: Modern format with excellent compression

**Video Output Formats:**
- **MP4**: Most compatible, good compression
- **MOV**: High quality, good for editing workflows
- **AVI**: Uncompressed option for maximum quality

**Video Codecs:**
- **H.265 (HEVC)**: Best compression and quality (recommended)
- **H.264**: Wide compatibility
- **ProRes**: Professional editing workflows

Choose based on your downstream workflow requirements and compatibility needs.

## API Documentation

For detailed API documentation and advanced usage, visit the [Topaz Labs API Documentation](https://www.topazlabs.com/).
