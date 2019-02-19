import setuptools

# Current directory must be data-labs repo before running setup.py!
with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="wellcome-policytool",
    version="0.0.1",
    author="Wellcome Trust Data Labs Team",
    author_email=" datalabs-engineering@wellcomecloud.onmicrosoft.com",
    description="Wellcome Trust Data Labs Policy Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellcometrust/data-labs/common",
    packages=setuptools.find_packages(
        # TODO: replace this when everything goes into policytool/
        # and our setup.py moves from policytool/policytool/setup.py
        # to policytool/setup.py. (in top level of repo)
        include=["scraper.*"]
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    tests_require=[
        'pytest',
    ],
    install_requires=[
        'apache-airflow',  # pulls in lxml for us
        'apache-airflow[crypto]',
        'boto3',
        'cryptography',
        'numpy',
        'pandas',
        'psycopg2-binary',
        'PyJWT',
        'requests',
        'scipy',
        'Scrapy',
        'sentry-sdk',
    ]
)
