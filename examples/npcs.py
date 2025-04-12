import asyncio
from dankmemer import DankMemerClient, NPCsFilter, Fuzzy, IN, ItemsFilter

async def main():
    async with DankMemerClient(cache_ttl_hours=1, useAntirateLimit=True) as client:
        # Example 1: Retrieve all NPCs
        all_npcs = await client.npcs.query()
        print("Example 1: All NPCs:", [npc.name for npc in all_npcs])
        
        # Example 2: Filter by exact id (e.g. "chad")
        filter_by_id = NPCsFilter(id="chad")
        npcs_by_id = await client.npcs.query(filter_by_id)
        print("Example 2: NPC with id 'chad':", [npc.name for npc in npcs_by_id])
        
        # Example 3: Fuzzy matching on NPC name (e.g. match names similar to "crypto")
        fuzzy_name_filter = NPCsFilter(name=Fuzzy("crypto", cutoff=70))
        npcs_fuzzy_name = await client.npcs.query(fuzzy_name_filter)
        print("Example 3: NPCs with fuzzy name 'crypto':", [npc.name for npc in npcs_fuzzy_name])
        
        # Example 4: Fuzzy matching on extra.bio (e.g. match bios containing "fishing")
        fuzzy_bio_filter = NPCsFilter(bio=Fuzzy("fishing", cutoff=60))
        npcs_by_bio = await client.npcs.query(fuzzy_bio_filter)
        print("Example 4: NPCs with bio matching 'fishing':", [npc.name for npc in npcs_by_bio])
        
        # Example 5: Filtering based on a location in extra.locations (e.g. "river")
        location_filter = NPCsFilter(locations="river")
        npcs_by_location = await client.npcs.query(location_filter)
        print("Example 5: NPCs with location 'river':", [npc.name for npc in npcs_by_location])



        # Using the new IN filter for NPC names
        print(
            [
                e.name for e in (
                await client.items.query(ItemsFilter(name=IN("melmsie", "appl")))
                )
            ]
        )
        # with context menu list comp

        print(
            [e.name async for e in client.items.iter_query(ItemsFilter(name=IN("melmsie", "appl")))] 
        )
        
        # without list comp

        async for e in client.items.iter_query(ItemsFilter(limit=5)):
            print(e.name) 

        print(
            [
                e.name for e in (
                await client.npcs.query(NPCsFilter(name=IN("chad")))
                )
            ]
        )

        
asyncio.run(main())
