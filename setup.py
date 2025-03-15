"""
Setup script for the documentor package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="documentor",
    version="0.1.0",
    author="Documetor Team",
    author_email="info@documentor.example.com",
    description="Document embeddings and semantic search with Google Vertex AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/documentor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyPDF2>=3.0.0",
        "python-docx>=0.8.11",
        "numpy>=1.22.0",
        "tqdm>=4.64.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "google-cloud-storage>=2.7.0",
        "google-cloud-aiplatform>=1.35.0",
    ],
    extras_require={
        "ocr": ["pytesseract>=0.3.10", "pdf2image>=1.16.0"],
        "dev": ["pytest>=7.0.0", "black>=22.3.0", "isort>=5.10.1", "mypy>=0.942"],
    },
    entry_points={
        "console_scripts": [
            "documentor=documentor.cli:app",
        ],
    },
)
