import asyncio
import websockets
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AISSTREAM_API_KEY")

if API_KEY:
    print(f"Using AISSTREAM_API_KEY: {API_KEY[:4]}...")
else:
    print("WARNING: AISSTREAM_API_KEY is not set!")

vessels = {}
history = {}
MAX_HISTORY = 100


async def connect_ais_stream():
    print("AIS RECEIVED MESSAGE")
    print(vessels)
    while True:
        try:
            async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:

                subscribe_message = {
                    "APIKey": API_KEY,
                    "BoundingBoxes": 
                        [
                    [[42.827639, 25.718994],
                     [45.970243, 33.711548]]
                        ],
                    "FilterMessageTypes": ["PositionReport"]
                }

                await websocket.send(json.dumps(subscribe_message))

                async for message_json in websocket:
                    message = json.loads(message_json)

                    try:
                        ais = message["Message"]["PositionReport"]
                    except Exception:
                        continue

                    mmsi = ais["UserID"]

                    point = {
                        "mmsi": mmsi,
                        "lat": ais["Latitude"],
                        "lon": ais["Longitude"],
                        "course": ais.get("Cog", 0),
                        "speed": ais.get("Sog", 0),
                        "timestamp": datetime.now(timezone.utc).timestamp()
                    }

                    vessels[mmsi] = point

                    if mmsi not in history:
                        history[mmsi] = []

                    history[mmsi].append([point["lat"], point["lon"]])

                    if len(history[mmsi]) > MAX_HISTORY:
                        history[mmsi].pop(0)

        except Exception as e:
            print(f"AIS stream error: {e}")
            await asyncio.sleep(5)