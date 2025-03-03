from setuptools import setup, find_packages

setup(
    name="membase",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},

    description="Add your description here",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    python_requires=">=3.10",
    install_requires=[],
) 