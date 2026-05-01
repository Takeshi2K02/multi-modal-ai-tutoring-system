import os

path = 'db/connection.py'
with open(path, 'rb') as f:
    content = f.read()

target = b"""        # tlsCAFile=certifi.where() fixes SSL certificate verify failed on Mac
        client = MongoClient(
            MONGO_URI, 
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )"""

# Support both \n and \r\n
target_lf = target.replace(b'\r\n', b'\n')
target_crlf = target.replace(b'\n', b'\r\n')

replacement = b"""        # Fix: SSL only for remote connections
        client_options = {"serverSelectionTimeoutMS": 5000}
        if "mongodb+srv" in MONGO_URI or "ssl=true" in MONGO_URI.lower():
            import certifi
            client_options["tlsCAFile"] = certifi.where()
            client_options["tls"] = True
        client = MongoClient(MONGO_URI, **client_options)"""

if target_lf in content:
    content = content.replace(target_lf, replacement.replace(b'\n', b'\n'))
elif target_crlf in content:
    content = content.replace(target_crlf, replacement.replace(b'\n', b'\r\n'))
else:
    print("Target not found exactly. Trying simpler match.")
    # Fallback to a simpler match
    content = content.replace(b'tlsCAFile=certifi.where()', b'# tlsCAFile removed for local')

with open(path, 'wb') as f:
    f.write(content)
print("Patched")
