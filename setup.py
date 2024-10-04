from setuptools import find_packages, setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="langsecure",
    version="0.1",
    description="security overlay for the lang resources.",
    author="ahmed",
    long_description=long_description,
    long_description_content_type="text/markdown",    
    author_email="ahmed@dkube.io",
    url="https://github.com/mahmedk/langsecure.git",
    packages=find_packages(),
    include_package_data=True,
    install_requires=required,
    python_requires=">=3.10",
    extras_require={}
)
