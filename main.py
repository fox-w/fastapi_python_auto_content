import os
import uuid
import tempfile
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from text_image_generator import create_text_image

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
        
        # Generate the image
        create_text_image(
            text=quote.text,
            output_filename=temp_filename,
            logo_path=logo_path,
            add_logo=True
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