# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package contains the auto JavaScript documentation Sphinx extension.
'''

requires = ['Sphinx>=0.6']

setup(
    name='sphinxcontrib-autojs',
    version='0.1',
    url='http://bitbucket.org/birkenfeld/sphinx-contrib',
    download_url='http://pypi.python.org/pypi/sphinxcontrib-autojs',
    license='BSD',
    author='Lee Heung-sub',
    author_email='sublee@lunant.com',
    description='Sphinx "Auto JavaScript Document" extension',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
)
