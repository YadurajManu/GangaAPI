from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import aiofiles
from datetime import datetime
import logging
from database import DatabaseManager
from config import UPLOAD_FOLDER, MAX_FILE_SIZE, HOST, PORT
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="ESP32-CAM Image Upload API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mount static files for serving images
app.mount("/images", StaticFiles(directory=UPLOAD_FOLDER), name="images")

# Database manager instance
db_manager = DatabaseManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    if not db_manager.connect():
        logger.error("Failed to connect to database on startup")
    else:
        logger.info("Database connected successfully on startup")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db_manager.disconnect()
    logger.info("Database disconnected on shutdown")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ESP32-CAM Image Upload API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "images": "/images",
            "image_by_id": "/images/{image_id}",
            "delete": "/images/{image_id}/delete"
        }
    }

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(""),
    location: str = Form("")
):
    """
    Upload image from ESP32-CAM or any client
    """
    try:
        # Validate file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
            )
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Insert metadata into database
        image_data = db_manager.insert_image_metadata(
            filename=file.filename or unique_filename,
            description=description,
            location=location,
            file_path=f"/images/{unique_filename}"
        )
        
        if not image_data:
            # If database insert fails, delete the file
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to save image metadata")
        
        logger.info(f"Image uploaded successfully: {unique_filename}")
        
        return {
            "message": "Image uploaded successfully",
            "image_id": image_data["id"],
            "filename": image_data["filename"],
            "path": image_data["path"],
            "uploaded_at": image_data["uploaded_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/images")
async def get_all_images():
    """
    Get all images metadata
    """
    try:
        images = db_manager.get_all_images()
        return {
            "message": "Images retrieved successfully",
            "count": len(images),
            "images": images
        }
    except Exception as e:
        logger.error(f"Error retrieving images: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve images")

@app.get("/images/{image_id}")
async def get_image_by_id(image_id: int):
    """
    Get specific image metadata by ID
    """
    try:
        image = db_manager.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "message": "Image retrieved successfully",
            "image": image
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")

@app.delete("/images/{image_id}/delete")
async def delete_image(image_id: int):
    """
    Delete image and its metadata
    """
    try:
        # Get image data first
        image = db_manager.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete from database
        if db_manager.delete_image(image_id):
            # Delete file from disk
            file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image["path"]))
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
            
            return {
                "message": "Image deleted successfully",
                "image_id": image_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete image")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_manager.connection else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
