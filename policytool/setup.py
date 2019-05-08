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
    name="wellcome-policytool",
    version="0.0.1",
    author="Wellcome Trust Data Labs Team",
    author_email="datalabs-engineering@wellcomecloud.onmicrosoft.com",
    description="Wellcome Trust Data Labs Policy Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellcometrust/data-labs/common",
    packages=setuptools.find_packages(
        # TODO: replace this when everything goes into policytool/
        # and our setup.py moves from policytool/policytool/setup.py
        # to policytool/setup.py. (in top level of repo)
        #
        # Until then, note well: the packages below are *not* within
        # the policytool namespace. So, don't do:
        #
        # >>> import policytool.scraper
        #
        # Instead, for now, do:
        #
        # >>> import scraper
        include=["pdf_parser.*", "scraper.*", "web.*"]
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
