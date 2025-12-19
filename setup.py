from setuptools import setup, find_packages

setup(
    name="neufox-honeypot-cog",
    version="1.0.0",
    description="A Red bot honeypot cog that bans users who talk in a trap channel.",
    author="itsneufox",
    author_email="shout@neufox.com",
    url="https://github.com/itsneufox/neufox-honeypot-cog",
    packages=find_packages(),
    install_requires=[
        "redbot>=3.5.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
