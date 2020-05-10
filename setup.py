from setuptools import setup

with open('requirements.txt') as req_files:
    requirements = req_files.read().splitlines()

setup(
    name='Outage Detector',
    version='1.0.0',
    packages=['outagedetector'],
    install_requires=requirements,
    entry_points={
        'console_scripts':[
            'outage_detector = outagedetector.__main__:main'
        ]
    },
    author='Butean Fabian'
)
