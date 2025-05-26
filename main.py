import os
import uuid
import tempfile
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from text_image_generator import create_text_image
from PIL import ImageFont

app = FastAPI(title="Quote Image Generator API", 
              description="API for generating and uploading quote images to Cloudinary")

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

class QuoteRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "Quote Image Generator API is running. Use /generate endpoint to create images."}

@app.get("/debug-fonts")
async def debug_fonts():
    """Endpoint to debug available fonts on the server"""
    font_info = {
        "system_fonts": [],
        "pillow_default": str(ImageFont.load_default()),
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown")
    }
    
    # Check common font directories
    font_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        "/Library/Fonts",  # macOS
        "C:\\Windows\\Fonts",  # Windows
        os.path.join(os.path.dirname(__file__), "fonts")  # Local fonts directory
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
    
    return font_info

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