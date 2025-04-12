Examples
========

Below are various examples demonstrating different filtering techniques for both Items and NPCs

Items Examples
--------------

1. **Exact String Matching**

   .. code-block:: python

       filtered = await client.items.query(ItemsFilter(name="Trash"))
       print([e.name for e in filtered])

2. **Fuzzy Matching on Item Name**

   .. code-block:: python

       filtered = await client.items.query(ItemsFilter(name=Fuzzy("trash", cutoff=80)))
       print([e.name for e in filtered])

3. **Membership Matching Using IN**

   .. code-block:: python

       filtered = await client.items.query(ItemsFilter(name=IN("melmsie", "appl")))
       print([e.name for e in filtered])

4. **Numeric Range Filtering**

   .. code-block:: python

       filtered = await client.items.query(ItemsFilter(marketValue=(5000, 10000000)))
       print([e.name for e in filtered])

5. **Numeric Filtering with Above/Below/Range**

   .. code-block:: python
    
       # Above
       filtered = await client.items.query(ItemsFilter(netValue=Above(10000)))
       print([e.name for e in filtered])

       # Below
       filtered = await client.items.query(ItemsFilter(netValue=Below(10000)))
       print([e.name for e in filtered])
    
       # Range 
       filtered = await client.items.query(ItemsFilter(netValue=Range(10000, 5000000)))
       print([e.name for e in filtered])

NPCs Examples
-------------

1. **Exact String Matching on NPC Name**

   .. code-block:: python

       filtered = await client.npcs.query(NPCsFilter(name="Chad"))
       print([e.name for e in filtered])

2. **Fuzzy Matching on NPC Name**

   .. code-block:: python

       filtered = await client.npcs.query(NPCsFilter(name=Fuzzy("chad", cutoff=75)))
       print([e.name for e in filtered])

3. **Membership Matching for NPCs**

   .. code-block:: python

       filtered = await client.npcs.query(NPCsFilter(name=IN("chad", "brad")))
       print([e.name for e in filtered])

4. **Numeric Range Filtering on NPC Reputation**

   .. code-block:: python

       filtered = await client.npcs.query(NPCsFilter(reputation=(10, 50)))
       print([e.name for e in filtered])

5. **Combining Filters for NPCs**

   .. code-block:: python

       filtered = await client.npcs.query(NPCsFilter(name=IN("chad"), reputation=Above(20)))
       print([e.name for e in filtered])
