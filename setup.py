from setuptools import setup

with open('requirements.txt') as req_files:
    requirements = req_files.read().splitlines()

with open("README.md", 'r') as readme:
    long_description = readme.read()

setup(
    name='Outage Detector',
    version='1.0.1',
    description='A module helping you find out when internet and power outages happen.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=['outagedetector'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'outage_detector = outagedetector.__main__:main'
        ]
    },
    author='Butean Fabian',
    author_email='buteanfabian@gmail.com'
)
