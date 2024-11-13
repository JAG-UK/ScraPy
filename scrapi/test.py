"""Simple test for end-to-end happy day cases"""

from pprint import pprint
import sys
import time

from scrapi import Scrapi

# args = {
#     "url": "https://app.dev-robin-0.dev.datatrails.ai",
#     "client_secret": "a18e91fa9757a4172b001089e74c5ba54a9fbfbc39133051547b495c48e1dc2e",
#     "client_id": "b27d6150-6087-4d42-9eb6-7f36597320e3",
#     "log_level": "DEBUG",
# }

args = {
  'url': 'https://app.datatrails.ai',
  'client_secret': '182e87770eb29c8068281ce00f53338f545b9d27b743494b08488a0fa55e654c',
  'client_id': 'a3b088b0-6123-4fb0-90ae-76d3d3bdff08',
  'log_level': 'DEBUG'
}

print("Initializing TS connection")
myScrapi = Scrapi("DataTrails", args)
print(myScrapi)

print("Registering Signed Statement")
# Read the binary data from the file
with open("signed-statement.cbor", "rb") as data_file:
    data = data_file.read()
    # Send to SCITT Transparency Service
    lro = myScrapi.register_signed_statement(data)
    if not lro:
        print("FATAL: failed to get registration ID for Signed Statement")
        sys.exit()

print("Polling operation status")
# Check on the status of the operation
# Poll until success or failure
while True:
    reg_result = myScrapi.check_registration(lro)
    print(reg_result)

    if not "status" in reg_result:
        print("This shouldn't happen!")
        # May be transient. Go round again
    elif reg_result["status"] == "failed":
        print("Registration FAILED :-(")
        sys.exit(1)
    elif reg_result["status"] == "running":
        print("STILL RUNNING :-|")
    elif reg_result["status"] == "succeeded":
        print("SUCCESS :-)")
        break
    else:
        print(f"This shouldn't happen! What is status '{reg_result['status']}'")
        # May be transient. Go round again

    time.sleep(2)

print("Next we fetch the receipt!")
receipt = myScrapi.resolve_receipt(reg_result["entryID"])
print(receipt)
pprint(receipt)
# Write out the updated Transparent Statement
with open("final_receipt", "wb") as file:
    file.write(receipt)
    print("File saved successfully")


print("Now see if we can get the original Signed Statement back")
signed_statement = myScrapi.resolve_signed_statement(reg_result["entryID"])
print(signed_statement)
