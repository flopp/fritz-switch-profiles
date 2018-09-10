import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fritz-switch-profiles",
    version="0.0.2",
    author="Kevin Eifinger",
    author_email="k.eifinger@googlemail.com",
    description="A (Python) script to remotely set device profiles of an AVM Fritz!Box",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eifinger/fritz-switch-profiles",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
   'requests',
   'lxml'
    ]
)