from setuptools import setup, find_packages

setup(
    name="esp32-cam-api",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "python-multipart",
        "psycopg2-binary",
        "python-dotenv",
        "Pillow",
        "aiofiles",
        "gunicorn",
    ],
    python_requires=">=3.11",
)
