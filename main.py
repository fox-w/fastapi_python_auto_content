import os
import uuid
import tempfile
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from text_image_generator import create_text_image
from motivational_video_editor import create_seamless_video_compilation
from PIL import ImageFont

app = FastAPI(title="Content Generator API", 
              description="API for generating quote images and seamless videos")

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

class QuoteRequest(BaseModel):
    text: str

class VideoRequest(BaseModel):
    video_urls: List[str]
    audio_url: Optional[str] = None
    format_mode: Optional[str] = "vertical"  # "vertical", "horizontal", or "auto"
    apply_moody_effect: Optional[bool] = False
    moody_intensity: Optional[float] = 0.7
    video_audio_volume: Optional[float] = 0.8
    background_music_volume: Optional[float] = 0.3

@app.get("/")
async def root():
    return {"message": "Content Generator API is running. Use /generate for images or /generate-sf-videos for seamless videos."}

@app.get("/debug-fonts")
async def debug_fonts():
    """Endpoint to debug available fonts on the server"""
    import subprocess
    import sys
    
    font_info = {
        "system_fonts": [],
        "pillow_default": str(ImageFont.load_default()),
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown"),
        "system_info": {
            "platform": sys.platform,
            "python_version": sys.version
        }
    }
    
    # Try to find fonts using system commands
    try:
        # Try fc-list command (common on Linux)
        result = subprocess.run(['fc-list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            fonts = result.stdout.split('\n')[:20]  # Limit to first 20
            font_info["fc_list"] = fonts
    except Exception as e:
        font_info["fc_list_error"] = str(e)
    
    # Check common font directories
    font_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        "/Library/Fonts",  # macOS
        "C:\\Windows\\Fonts",  # Windows
        "/app/fonts",  # Local fonts directory in container
        "/system/fonts",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/TTF"
    ]
    
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            font_info["system_fonts"].append({
                "directory": font_dir,
                "exists": True,
                "files": []
            })
            
            # Try to list fonts in this directory and subdirectories
            try:
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if file.lower().endswith(('.ttf', '.otf')):
                            font_info["system_fonts"][-1]["files"].append(
                                os.path.join(root, file)
                            )
                            # Limit to first 20 fonts to avoid huge response
                            if len(font_info["system_fonts"][-1]["files"]) >= 20:
                                font_info["system_fonts"][-1]["files"].append("... and more")
                                break
                    if len(font_info["system_fonts"][-1]["files"]) >= 20:
                        break
            except Exception as e:
                font_info["system_fonts"][-1]["error"] = str(e)
        else:
            font_info["system_fonts"].append({
                "directory": font_dir,
                "exists": False
            })
    
    # Try to get info about the default font
    try:
        default_font = ImageFont.load_default()
        font_info["default_font_path"] = getattr(default_font, 'path', 'No path attribute')
        font_info["default_font_size"] = getattr(default_font, 'size', 'No size attribute')
    except Exception as e:
        font_info["default_font_error"] = str(e)
    
    return font_info

@app.get("/debug-ffmpeg")
async def debug_ffmpeg():
    """Endpoint to debug FFMPEG version and codec support on the server"""
    import subprocess
    import sys
    import os
    
    ffmpeg_info = {
        "system_info": {
            "platform": sys.platform,
            "python_version": sys.version
        },
        "moviepy_info": {},
        "ffmpeg_info": {}
    }
    
    # Check MoviePy version and config
    try:
        import moviepy
        ffmpeg_info["moviepy_info"]["version"] = moviepy.__version__
        
        # Check MoviePy's FFMPEG config
        from moviepy.config import FFMPEG_BINARY
        ffmpeg_info["moviepy_info"]["ffmpeg_binary"] = FFMPEG_BINARY
        
        # Test MoviePy's bundled FFMPEG directly
        if FFMPEG_BINARY and os.path.exists(FFMPEG_BINARY):
            ffmpeg_info["moviepy_info"]["bundled_ffmpeg_exists"] = True
            try:
                result = subprocess.run([FFMPEG_BINARY, '-version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    ffmpeg_info["moviepy_info"]["bundled_ffmpeg_version"] = lines[:3]
                else:
                    ffmpeg_info["moviepy_info"]["bundled_ffmpeg_error"] = result.stderr
            except Exception as e:
                ffmpeg_info["moviepy_info"]["bundled_ffmpeg_test_error"] = str(e)
        else:
            ffmpeg_info["moviepy_info"]["bundled_ffmpeg_exists"] = False
            
    except Exception as e:
        ffmpeg_info["moviepy_info"]["error"] = str(e)
    
    # Check FFMPEG version (system)
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            ffmpeg_info["ffmpeg_info"]["version_output"] = lines[:5]  # First 5 lines
        else:
            ffmpeg_info["ffmpeg_info"]["error"] = f"ffmpeg command failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        ffmpeg_info["ffmpeg_info"]["error"] = "ffmpeg command timed out"
    except FileNotFoundError:
        ffmpeg_info["ffmpeg_info"]["error"] = "ffmpeg binary not found"
    except Exception as e:
        ffmpeg_info["ffmpeg_info"]["error"] = str(e)
    
    # Check available codecs using bundled FFMPEG
    try:
        from moviepy.config import FFMPEG_BINARY
        if FFMPEG_BINARY:
            result = subprocess.run([FFMPEG_BINARY, '-codecs'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Look for h264 codec specifically
                codec_lines = result.stdout.split('\n')
                h264_lines = [line for line in codec_lines if 'h264' in line.lower()]
                ffmpeg_info["ffmpeg_info"]["h264_codecs"] = h264_lines[:5]
            else:
                ffmpeg_info["ffmpeg_info"]["codecs_error"] = result.stderr
    except Exception as e:
        ffmpeg_info["ffmpeg_info"]["codecs_error"] = str(e)
    
    # Test basic MoviePy functionality
    try:
        from moviepy import VideoFileClip
        import tempfile
        import os
        
        ffmpeg_info["moviepy_info"]["import_success"] = True
        
        # Test with a simple video URL (if we can find one)
        test_url = "https://res.cloudinary.com/das3qd7oa/video/upload/v1749125992/willink_do_you_actually_want_to_do_it_longer_uuyxk7.mp4"
        ffmpeg_info["video_test"] = {
            "test_url": test_url,
            "status": "attempting_download"
        }
        
        try:
            # Try to download and test one video
            from motivational_video_editor import download_media_from_url
            
            print("Testing video download and loading...")
            temp_path = download_media_from_url(test_url, 'mp4')
            ffmpeg_info["video_test"]["download_success"] = True
            ffmpeg_info["video_test"]["file_size"] = os.path.getsize(temp_path)
            
            # Try to load with MoviePy
            clip = VideoFileClip(temp_path, audio=False)
            ffmpeg_info["video_test"]["moviepy_load_success"] = True
            ffmpeg_info["video_test"]["duration"] = clip.duration
            ffmpeg_info["video_test"]["size"] = clip.size
            
            # Try to read first frame
            first_frame = clip.get_frame(0)
            ffmpeg_info["video_test"]["first_frame_success"] = True
            ffmpeg_info["video_test"]["frame_shape"] = first_frame.shape
            
            clip.close()
            os.unlink(temp_path)
            
        except Exception as video_error:
            ffmpeg_info["video_test"]["error"] = str(video_error)
            
            # If first frame failed, try alternative approaches
            try:
                # Try loading without frame validation
                clip = VideoFileClip(temp_path, audio=False)
                ffmpeg_info["video_test"]["clip_load_without_frame_test"] = True
                ffmpeg_info["video_test"]["duration_alt"] = clip.duration
                ffmpeg_info["video_test"]["size_alt"] = clip.size
                
                # Try reading frame at middle of video
                if clip.duration > 1:
                    mid_frame = clip.get_frame(clip.duration / 2)
                    ffmpeg_info["video_test"]["mid_frame_success"] = True
                    ffmpeg_info["video_test"]["mid_frame_shape"] = mid_frame.shape
                
                # Try a basic resize operation to see if processing works
                resized_clip = clip.resized((640, 360))
                ffmpeg_info["video_test"]["resize_test_success"] = True
                ffmpeg_info["video_test"]["resized_size"] = resized_clip.size
                
                clip.close()
                resized_clip.close()
                os.unlink(temp_path)
                
                ffmpeg_info["video_test"]["bypass_first_frame_success"] = True
                
            except Exception as alt_error:
                ffmpeg_info["video_test"]["alternative_error"] = str(alt_error)
                try:
                    if 'temp_path' in locals() and os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
            
    except Exception as e:
        ffmpeg_info["moviepy_info"]["import_error"] = str(e)
    
    return ffmpeg_info

@app.post("/generate")
async def generate_image(quote: QuoteRequest):
    """
    Generate an image with the provided quote text and upload it to Cloudinary.
    
    The quote text can include:
    - {word} for bold text
    - \\n for line breaks
    
    Returns the Cloudinary URL of the uploaded image.
    """
    try:
        # Create a temporary file for the image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Create the image with default settings
        logo_path = "visionary.mindset_logo.png"  # Using the logo in the root directory
        
        # Try to find a reliable font that should be available on most systems
        font_path = None
        
        # Common fonts to try in order of preference
        common_fonts = [
            os.path.join(os.path.dirname(__file__), "fonts", "AncizarSerif-Regular.ttf"),  # Bundled font (highest priority)
            os.path.join(os.path.dirname(__file__), "fonts", "AncizarSerif-Bold.ttf"),  # Bundled bold font
            os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Regular.ttf"),  # Bundled font backup
            os.path.join(os.path.dirname(__file__), "fonts", "Arial.ttf"),  # Local font if you added it
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Common on Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Common on Linux
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",  # Another Linux path
            "/Library/Fonts/Arial.ttf",  # macOS
            "C:\\Windows\\Fonts\\arial.ttf"  # Windows
        ]
        
        for font in common_fonts:
            if os.path.exists(font):
                font_path = font
                print(f"Using font: {font_path}")
                break
        
        if not font_path:
            print("No specific font found, using default")
        
        # Generate the image
        create_text_image(
            text=quote.text,
            output_filename=temp_filename,
            logo_path=logo_path,
            add_logo=True,
            font_path=font_path
        )
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            temp_filename,
            folder="quote_images",
            public_id=f"quote_{uuid.uuid4().hex[:8]}"
        )
        
        # Clean up the temporary file
        os.unlink(temp_filename)
        
        # Return the Cloudinary URL
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.post("/generate-sf-videos")
async def generate_seamless_videos(request: VideoRequest):
    """
    Generate a seamless video compilation from video URLs with optional background music and upload to Cloudinary.
    
    Args:
        video_urls: List of video URLs to download and combine
        audio_url: Optional URL for background music/audio
        format_mode: Output format - "vertical" (1080x1920), "horizontal" (1920x1080), or "auto"
        apply_moody_effect: Whether to apply dark moody visual effect
        moody_intensity: Intensity of moody effect (0.0-1.0)
        video_audio_volume: Volume level for original video audio (0.0-1.0)
        background_music_volume: Volume level for background music (0.0-1.0)
    
    Returns:
        Cloudinary URL of the uploaded video and processing details
    """
    try:
        # Log the incoming request for debugging
        print("=== INCOMING REQUEST ===")
        print(f"Video URLs count: {len(request.video_urls)}")
        for i, url in enumerate(request.video_urls):
            print(f"  Video {i+1}: {url[:100]}{'...' if len(url) > 100 else ''}")
        print(f"Audio URL: {request.audio_url}")
        print(f"Format mode: {request.format_mode}")
        print(f"Moody effect: {request.apply_moody_effect}")
        print(f"Moody intensity: {request.moody_intensity}")
        print(f"Video audio volume: {request.video_audio_volume}")
        print(f"Background music volume: {request.background_music_volume}")
        print("========================")
        
        # Validate input
        if not request.video_urls or len(request.video_urls) < 1:
            error_msg = "At least one video URL is required"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if len(request.video_urls) > 10:  # Reasonable limit
            error_msg = "Maximum 10 videos allowed per compilation"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check for malformed URLs (common issue with make.com)
        for i, url in enumerate(request.video_urls):
            if ',' in url and url.count('http') > 1:
                error_msg = f"Video URL {i+1} appears to contain multiple URLs separated by commas. Please provide each URL as a separate array element."
                print(f"❌ URL Format Error: {error_msg}")
                print(f"   Problematic URL: {url}")
                raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate format mode
        valid_formats = ["vertical", "horizontal", "auto"]
        if request.format_mode not in valid_formats:
            error_msg = f"format_mode must be one of: {valid_formats}"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate volume levels
        if not (0.0 <= request.video_audio_volume <= 1.0):
            error_msg = "video_audio_volume must be between 0.0 and 1.0"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if not (0.0 <= request.background_music_volume <= 1.0):
            error_msg = "background_music_volume must be between 0.0 and 1.0"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if not (0.0 <= request.moody_intensity <= 1.0):
            error_msg = "moody_intensity must be between 0.0 and 1.0"
            print(f"❌ Validation Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        print(f"✅ Validation passed. Processing video compilation request with {len(request.video_urls)} videos")
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_output_path = temp_file.name
        
        try:
            print(f"📁 Created temporary output file: {temp_output_path}")
            
            # Create the seamless video compilation
            print("🎬 Starting video compilation...")
            video_path = create_seamless_video_compilation(
                video_urls=request.video_urls,
                audio_url=request.audio_url,
                output_path=temp_output_path,
                format_mode=request.format_mode,
                apply_moody_effect=request.apply_moody_effect,
                moody_intensity=request.moody_intensity,
                video_audio_volume=request.video_audio_volume,
                background_music_volume=request.background_music_volume
            )
            
            print("☁️ Uploading video to Cloudinary...")
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                video_path,
                folder="generated_sf_video",
                public_id=f"seamless_video_{uuid.uuid4().hex[:8]}",
                resource_type="video",
                eager=[
                    {"quality": "auto", "fetch_format": "mp4"},
                    {"quality": "auto:low", "fetch_format": "mp4", "width": 640, "crop": "scale"}
                ]
            )
            
            print(f"✅ Video uploaded successfully: {result['secure_url']}")
            
            # Return the result - simplified response
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"]
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_output_path):
                print(f"🧹 Cleaning up temporary file: {temp_output_path}")
                os.unlink(temp_output_path)
                
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        error_msg = f"Video generation failed: {str(e)}"
        print(f"💥 FATAL ERROR: {error_msg}")
        print("🔍 Full error details:")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)