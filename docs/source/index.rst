.. dankmemer.py documentation master file, created by
   sphinx-quickstart on Tue Apr  8 16:51:49 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to dankmemer.py's Documentation!
==========================================

This is the official documentation for dankmemer.py, an asynchronous Python wrapper for the DankAlert API.

Contents
--------
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api

Installation
------------
You can install dankmemer.py via pip:

.. code-block:: bash

   pip install dankmemer.py

Quick Example
-------------
Below is a basic usage example that demonstrates how to query the `/items` endpoint, apply filtering with the `ItemsFilter` class, and perform fuzzy matching using the `Fuzzy` helper.

.. code-block:: python

   import asyncio
   from dankmemer import DankMemerClient, ItemsFilter, Fuzzy

   async def main():
       async with DankMemerClient() as client:
           # Retrieve all items without filtering.
           all_items = await client.items.query()
           print("All items:", all_items)

           # Example: Filter items with:
           # - Fuzzy matching on the 'name' field.
           # - Boolean filtering on 'hasUse'.
           # - Numeric range filtering on 'marketValue'.
           filter_obj = ItemsFilter(
               name=Fuzzy("trash", cutoff=80),  # fuzzy match on name with 80% cutoff
               hasUse=False,                   # only items that are not usable
               marketValue=(5000, 10000000)      # marketValue between 5,000 and 10,000,000
           )

           filtered_items = await client.items.query(filter_obj)
           print("Filtered items:", filtered_items)

   asyncio.run(main())

Additional Information
----------------------
For a detailed description of each module and class, please refer to the API Reference above.

