#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup_requirements = []

test_requirements = []

setup(
    author="Andrew Creegan",
    author_email='andrew.s.creegan@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python package implementing a full featured producer/consumer pattern for concurrent workers",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='adv_prodcon',
    name='adv_prodcon',
    packages=find_packages(include=['adv_prodcon', 'adv_prodcon.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/acreegan/adv_prodcon',
    version='0.1.13',
    zip_safe=False,
)

if __name__ == '__main__':
    setup(
        name = "adv_prodcon",
    )
