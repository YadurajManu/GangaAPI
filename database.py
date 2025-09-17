import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("Database connected successfully")
            
            # Create images table if it doesn't exist
            self.create_images_table()
            
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def create_images_table(self):
        """Create images table if it doesn't exist"""
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS images (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    path TEXT
                );
            """
            self.cursor.execute(create_table_query)
            self.connection.commit()
            logger.info("Images table created or already exists")
        except Exception as e:
            logger.error(f"Failed to create images table: {e}")
            self.connection.rollback()
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database disconnected")
    
    def insert_image_metadata(self, filename, description, location, file_path):
        """Insert image metadata into the images table"""
        try:
            query = """
                INSERT INTO images (filename, description, location, uploaded_at, path)
                VALUES (%s, %s, %s, NOW(), %s)
                RETURNING id, filename, description, location, uploaded_at, path
            """
            self.cursor.execute(query, (filename, description, location, file_path))
            self.connection.commit()
            
            result = self.cursor.fetchone()
            logger.info(f"Image metadata inserted: {result['filename']}")
            return dict(result)
        except Exception as e:
            logger.error(f"Failed to insert image metadata: {e}")
            self.connection.rollback()
            return None
    
    def get_all_images(self):
        """Fetch all image metadata from the database"""
        try:
            query = """
                SELECT id, filename, description, location, uploaded_at, path
                FROM images
                ORDER BY uploaded_at DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            images = [dict(row) for row in results]
            logger.info(f"Retrieved {len(images)} images from database")
            return images
        except Exception as e:
            logger.error(f"Failed to fetch images: {e}")
            return []
    
    def get_image_by_id(self, image_id):
        """Fetch specific image metadata by ID"""
        try:
            query = """
                SELECT id, filename, description, location, uploaded_at, path
                FROM images
                WHERE id = %s
            """
            self.cursor.execute(query, (image_id,))
            result = self.cursor.fetchone()
            
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch image {image_id}: {e}")
            return None
    
    def delete_image(self, image_id):
        """Delete image metadata from database"""
        try:
            query = "DELETE FROM images WHERE id = %s"
            self.cursor.execute(query, (image_id,))
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Image {image_id} deleted from database")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            self.connection.rollback()
            return False
