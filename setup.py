"""
Sphinx "Auto JavaScript Document" extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package contains the auto JavaScript documentation Sphinx extension. See
the example: `The jDoctest documentation <http://jdoctest.lunant.org/>`_
that was generated from `jdoctest.js source file
<https://raw.github.com/lunant/jdoctest/master/jdoctest.js>`_.

Links
`````

* `GitHub repository <http://github.com/lunant/sphinxcontrib-autojs>`_
* `development version
  <http://github.com/lunant/sphinxcontrib-autojs/zipball/master#egg=sphinxcontrib-autojs-dev>`_

"""
from setuptools import setup, find_packages

requires = ['Sphinx>=0.6']

setup(
    name='sphinxcontrib-autojs',
    version='0.1',
    url='https://github.com/lunant/sphinxcontrib-autojs',
    download_url='http://pypi.python.org/pypi/sphinxcontrib-autojs',
    license='BSD',
    author='Heungsub Lee',
    author_email='h@subl.ee',
    description='Sphinx "Auto JavaScript Document" extension',
    long_description=__doc__,
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
