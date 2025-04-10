.. dankmemer.py documentation master file, created by
   sphinx-quickstart on Tue Apr  8 16:51:49 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

dankmemer.py Documentation
==========================

Welcome to the documentation for dankmemer.py, a lightweight asynchronous Python wrapper for the DankAlert API.
This alpha release currently supports the Items and NPC routes. Future releases will expand the API coverage.

Installation
------------
You can install dankmemer.py via pip:

.. code-block:: bash

   pip install dankmemer
   pip install dankmemer.py

Features
--------
- Built-in caching with configurable TTL
- Powerful filtering (exact, fuzzy, membership [IN], numeric range, Above/Below/Range)
- Anti-rate-limit protection

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   quickstart
   examples


.. toctree::
   :maxdepth: 2
   :caption: API Reference

   dankmemerclient
   routes
   objects
   exceptions


