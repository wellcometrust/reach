import setuptools

# Current directory must be data-labs repo before running setup.py!
with open("README.md", "r") as f:
    long_description = f.read()

with open('unpinned_requirements.txt') as f:
    unpinned_requirements = [
        l.strip() for l in f
        if not l.startswith('#')
    ]

setuptools.setup(
    name="wellcome-reach",
    version="0.0.1",
    author="Wellcome Trust Data Labs Team",
    author_email="datalabs-engineering@wellcomecloud.onmicrosoft.com",
    description="Wellcome Trust Data Labs Reach",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellcometrust/data-labs/common",
    packages=setuptools.find_packages(
        include=["reach.*"],
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    tests_require=[
        'pytest',
    ],
    install_requires=unpinned_requirements,
)
