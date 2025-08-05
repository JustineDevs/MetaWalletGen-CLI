from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="metawalletgen-cli",
    version="1.0.0",
    author="JustineDevs",
    author_email="contact@justinedevs.com",
    description="A secure CLI tool for generating Ethereum-compatible wallets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/justinedevs/metawalletgen-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "metawalletgen=metawalletgen.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ethereum wallet blockchain metamask cli",
    project_urls={
        "Bug Reports": "https://github.com/justinedevs/metawalletgen-cli/issues",
        "Source": "https://github.com/justinedevs/metawalletgen-cli",
        "Documentation": "https://github.com/justinedevs/metawalletgen-cli#readme",
    },
) 