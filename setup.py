from setuptools import setup, find_packages

setup(
    name="nv-cloud-function-helpers",
    version="0.0.1",
    description="A library with functions for NVCF",
    url="https://github.com/NVIDIA/nv-cloud-function-helpers",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.0.0",
        "Requests>=2.31.0",
        "numpy>=1.17",
    ],
    dependency_links=["https://pypi.ngc.nvidia.com"],
)
