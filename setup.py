from setuptools import setup, find_packages

setup(
    name="tapcheck-api",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask==2.3.3",
        "pandas==2.0.3",
        "numpy==1.24.3",
        "scikit-learn==1.3.0",
        "gunicorn==21.2.0"
    ],
    python_requires=">=3.11",
) 