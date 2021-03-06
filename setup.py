from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as req:
        content = req.read()
        requirements = content.split('\n')
    return requirements

setup(
    name="falcon_multiqc",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    classifiers=[
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
    ],
    entry_points="""
        [console_scripts]
        falcon_multiqc=falcon_multiqc.cli:safe_entry_point
    """
)