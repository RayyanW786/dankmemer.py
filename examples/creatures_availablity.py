import asyncio
from dankmemer import DankMemerClient

async def main():
    async with DankMemerClient(cache_ttl_hours=1, useAntirateLimit=True) as client:
        all_creatures = await client.creatures.query()
        print("Availability Windows (Current UTC Date):")
        for creature in all_creatures:
            try:
                start_dt, end_dt = creature.get_availability_window()
                # Format start and end times as 12-hour clock strings, stripping any leading zero.
                start_str = start_dt.strftime("%I %p").lstrip("0")
                end_str = end_dt.strftime("%I %p").lstrip("0")
                # If the end date is not the same as the start date, append "(tomorrow)"
                if start_dt.date() != end_dt.date():
                    end_str += " (tomorrow)"
                print(f"{creature.name}: Starts at {start_str} and ends at {end_str}")
            except ValueError as e:
                print(f"{creature.name}: No valid time info ({e})")

asyncio.run(main())
