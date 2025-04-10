dankmemer.py
============

**Alpha Release Notice:**
-------------------------

**dankmemer.py** is currently in alpha. At this stage, only the items and NPC routes are implemented.
Future releases will include additional routes and enhanced features.

**dankmemer.py** is a lightweight asynchronous Python wrapper for the
`DankAlert API <https://api.dankalert.xyz>`_ — it allows you to easily access Dank Memer-related data (such as items and NPCs) using powerful filtering and built-in caching.

🚀 Features
-----------

- Built-in caching with configurable TTL
- Powerful filtering with support for exact, fuzzy, membership (IN), and numeric range queries
- Anti-rate-limit handling

📦 Installation
---------------

You can install the project using either of the following aliases:

.. code-block:: bash

    pip install dankmemer
    pip install dankmemer.py

💡 Basic Usage Example
----------------------

Below are two examples that demonstrate filtering using the new interfaces.

**Example 1: Filtering Items**

.. code-block:: python

    # This example prints the names of items where the 'name' field contains either "melmsie" or "appl"
    print(
        [
            e.name for e in (
                await client.items.query(ItemsFilter(name=IN("melmsie", "appl")))
            )
        ]
    )

**Example 2: Filtering NPCs**

.. code-block:: python

    # This example prints the names of NPCs whose name contains the substring "chad"
    print(
        [
            e.name for e in (
                await client.npcs.query(NPCsFilter(name=IN("chad")))
            )
        ]
    )

Quick Start:
------------

Below is a minimal example that shows how to use the client with filtering:

.. code-block:: python

    import asyncio
    from dankmemer import DankMemerClient, ItemsFilter, NPCsFilter, Fuzzy, IN

    async def main():
        async with DankMemerClient() as client:
            # Query all items (no filtering)
            all_items = await client.items.query()
            print("All items:", all_items)

            # Query items with fuzzy matching on name.
            filtered_items = await client.items.query(ItemsFilter(name=Fuzzy("trash", cutoff=80)))
            print("Filtered items:", filtered_items)

            # Query NPCs with membership filtering on name.
            filtered_npcs = await client.npcs.query(NPCsFilter(name=IN("chad")))
            print("Filtered NPCs:", filtered_npcs)

    asyncio.run(main())

Documentation:
--------------

Full documentation is under development and will soon be available on Read the Docs at:

   https://dankmemerpy.readthedocs.io

Feel free to test, report issues, and contribute to this alpha release!


