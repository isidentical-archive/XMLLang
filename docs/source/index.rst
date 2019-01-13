Welcome to XMLLang's documentation!
===================================

XMLLang is a simple programming language that uses XML syntax 
and compiles to python bytecode. 

XMLLang.parser parses XML files with python's built-in xml parser
than generates a CST. Uses python's built-in AST module to transform
XMLLang CST to Python AST. 

XMLLang.compiler compiles generated python AST with python's built-in bytecode
compiler functions and executes it on CPython VM.

.. toctree::
   :glob:

   pages/*

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
