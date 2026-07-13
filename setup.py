#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    with open(filename) as f:
        lineiter = [line.strip() for line in f]
    return [line for line in lineiter if line and not line.startswith("#")]


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = parse_requirements("requirements.txt")

setup_requirements = [
    'pytest-runner',
    # put setup requirements (distutils extensions, etc.) here
]

test_requirements = parse_requirements("requirements_dev.txt")

setup(
    author="spade-rpc",
    author_email='n.garcia.sastre@gmail.com',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: XMPP',
    ],
    description="Plugin for SPADE platform to implement rpc protocol on agents",
    entry_points={
        'console_scripts': [
            'spade_rpc=spade_rpc.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='spade_rpc',
    name='spade_rpc',
    packages=find_packages(include=['spade_rpc', 'spade_rpc.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/javipalanca/spade_rpc',
    version='0.1.0',
    zip_safe=False,
)
