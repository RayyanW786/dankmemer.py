dankmemer.py
============

**Alpha Release Notice:**
-------------------------

**dankmemer.py** is currently in alpha. At this stage, only the items route is implemented. Future releases will include additional routes and enhanced features.

**dankmemer.py** is a simple and powerful asynchronous Python wrapper for the `DankAlert API <https://api.dankalert.xyz>`_ — giving you easy access to Dank Memer-related data like items, NPCs, skills, tools, and more.

🚀 Features
-----------

- Built-in caching with configurable TTL
- Powerful filtering with support for exact, fuzzy, and numeric range queries

📦 Installation
---------------

You can install the project using any of the following aliases:

.. code-block:: bash

    pip install dankmemer
    pip install dankmemer.py

Items Route
-----------

The Items Route provides access to the ``/items`` endpoint from the DankAlert API. It automatically caches responses for a configurable period, converts raw JSON into ``Item`` objects, and allows easy filtering via the ``ItemsFilter`` class and the ``Fuzzy`` helper.

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    from dankmemer import DankMemerClient, ItemsFilter, Fuzzy

    async def main():
        async with DankMemerClient() as client:
            # Retrieve all items without filtering.
            all_items = await client.items.query()
            print("All items:", all_items)

            # Example: Filtering items using various criteria:
            # - Fuzzy matching on the 'name' field (e.g. items with names similar to "trash")
            # - Boolean filtering for 'hasUse' flag
            # - Numeric range filtering for 'marketValue'
            filter_obj = ItemsFilter(
                name=Fuzzy("trash", cutoff=80),  # Fuzzy match on name with a cutoff of 80%
                hasUse=False,                    # Only items that are not usable
                marketValue=(5000, 10000000)      # Market value between 5,000 and 10,000,000
            )

            filtered_items = await client.items.query(filter_obj)
            print("Filtered items:", filtered_items)

    asyncio.run(main())

This basic example demonstrates:
- **Exact vs. Fuzzy Matching:** Use a plain string for exact matches (e.g. ``name="Trash"``) or wrap your string with the ``Fuzzy`` helper (e.g. ``name=Fuzzy("trash", cutoff=80)``) for fuzzy matching.
- **Numeric Range Filtering:** Supply a tuple ``(min, max)`` to filter numeric fields such as ``marketValue``.
- **Boolean Filtering:** Directly pass boolean values (e.g. ``hasUse=True``).

Documentation
-------------

Full documentation for dankmemer.py can be found at:

   https://dankmemer-py.readthedocs.io

Feel free to test, report issues, and contribute to this alpha release!

