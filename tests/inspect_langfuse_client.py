from langfuse import get_client
client = get_client()
print(f"Client type: {type(client)}")
print(f"Has score attribute: {hasattr(client, 'score')}")
print("Methods:", [m for m in dir(client) if not m.startswith('_')])
