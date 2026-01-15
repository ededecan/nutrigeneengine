from setuptools import setup, find_packages

setup(
    name="NutriGeneEngine",
    version="0.1.0",
    description="A lightweight, schema-driven Python engine for calculating personalized genetic risk scores for nutrition, athletic performance, and behavioral traits.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    readme="README.md",
    license="MIT",
    author="Enes Dedecan",
    author_email="enesdedecan@outlook.com",
    url="https://github.com/ededecan/nutrigeneengine",
    project_urls={
        "Homepage": "https://github.com/ededecan/nutrigeneengine",
        "Issues": "https://github.com/ededecan/nutrigeneengine/issues",
    },
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
        "reportlab>=4.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.990",
        ],
    },
)
