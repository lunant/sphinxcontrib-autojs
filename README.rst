.. -*- restructuredtext -*-

============================
Auto JavaScript Documentaion
============================

:author: Heungsub Lee <h@subl.ee>


This extension generates a reference documentation from a JavaScript source
file. A JavaScript source code should follow the style that is suggested by
`jDoctest`_.

.. _jDoctest: https://lunant.github.io/jdoctest/


Installation
============

Enter the ``sphinxcontrib-autojs`` directory and run:

.. sourcecode:: console

    $ python setup.py install


Usage
=====


Here is an example JavaScript source.

.. sourcecode:: js

    var ImageFile = function( url ) {
        /**class:ImageFile( url )

        A container for an image file.
            >>> var img = new ImageFile( "_static/jdoctest.png" );
            >>> img.url;
            '_static/jdoctest.png'
        */
        this.url = String( url );
    };
    ImageFile.prototype = {
        fetchData: function() {
            /**:ImageFile.prototype.fetchData()

            Request to the server to get data of this image file. When the
            request done we can get ``size`` or ``modified`` attribute.

                >>> img.fetchData();
                >>> wait(function() { return img.data; });
                >>> img.size;
                21618
                >>> img.modified; //doctest: +SKIP
                Sat Sep 25 2010 19:57:47 GMT+0900 (KST)
            */
            $.get( this.url, function( data ) {
                this.data = data;
                this.size = data.length;
                this.modified = new Date(); // Not Implemented Yet
            });
        }
    };

The file that has this source named ``imagefile.js``. It is in ``_examples``
directory of the current Sphinx document directory. Then this source:

.. sourcecode:: rst

    .. autojs:: _examples/imagefile.js

is rendered as:

.. autojs:: _examples/imagefile.js


JavaScript Docstring
--------------------

Here is the documentation of jDoctest which explains a JavaScript comment block
for docstring.

    A docstring is a multiline comment but it starts with ``/**``.

But this extension examines only named docstrings. A name of a docstring is
after ``/**`` and starts with ``:``:

.. sourcecode:: js

    /**:SomeClass.prototype.someMethod( reqArg[, optArg1[, optArg2 ] ] )

    The description for ``someMethod``.
    */

Then the example docstring's name is
``SomeClass.prototype.someMethod( reqArg[, optArg1[, optArg2 ] ] )``.


JavaScript Doctest
------------------

You might know `doctest`_ module for Python. This module examines interactive
Python sessions such as:

.. sourcecode:: pycon

    >>> [factorial(n) for n in range(6)]
    [1, 1, 2, 6, 24, 120]
    >>> [factorial(long(n)) for n in range(6)]
    [1, 1, 2, 6, 24, 120]
    >>> factorial(30)
    265252859812191058636308480000000L

The interactive JavaScript sessions are similar to the Python's:

.. sourcecode:: jscon

    >>> var title = $( "h1" );
    >>> title.click(function() {
    ...     alert( this.innerText );
    ... });
    [object Object]
    >>> Math.round( 1.11111111 );
    1

.. _doctest: http://docs.python.org/library/doctest


Options
-------

``:members:``:
    The member list in the source code. Each members are separated by a
    comma(``,``). A member is such as ``ImageFile`` or
    ``ImageFile.prototype.fetchData``. If you want to make a documentation
    of only ``ImageFile.prototype.fetchData`` then:

    .. sourcecode:: rst

        .. autojs:: _examples/imagefile.js
           :members: ImageFile.prototype.fetchData
