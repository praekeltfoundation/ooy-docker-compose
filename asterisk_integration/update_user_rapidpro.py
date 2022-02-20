#!/opt/rapidpro_connection/venv/bin/python
# import agi # This might be useful if we need to get variables from the dialplan
import os
import sys
from dotenv import load_dotenv
from temba_client.v2 import TembaClient

# Load environment variables
load_dotenv("/opt/rapidpro_connection/environment.env")
url = os.getenv("RAPIDPRO_URL")
token = os.getenv("RAPIDPRO_TOKEN")
flow_uuid = os.getenv("RAPIDPRO_FLOW")

client = TembaClient(url, token)

# Get arguments. Default direction to "inbound" in case it isn't set
msisdn = sys.argv[1]
call_start = sys.argv[2]
call_end = sys.argv[3]
direction = "inbound"
if len(sys.argv) > 4:
    direction = sys.argv[4]

# Format the msisdn to match Rapidpro
if msisdn[0] == "0":
    msisdn = "+254{}".format(msisdn[1:])
if msisdn[0] != "+":
    msisdn = "+{}".format(msisdn)
wa_id = msisdn.replace('+', '')  # Strip the + for WA
urns = ["tel:{}".format(msisdn), "whatsapp:{}".format(wa_id)]

# Check if the contact exists in Rapidpro, create it if not
contact = client.get_contacts(urn=urns[0]).first()
if not contact:
    contact = client.get_contacts(urn="whatsapp:{}".format(wa_id)).first()
if not contact:
    contact = client.create_contact(urns=urns)

# Start the contact on the flow that will store the details
client.create_flow_start(
    flow=flow_uuid,
    contacts=[contact],
    restart_participants=True,
    params={
        "call_start_time": call_start,
        "call_end_time": call_end,
        "direction": direction
    }
)
