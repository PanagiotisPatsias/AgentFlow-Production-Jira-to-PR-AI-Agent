from agentflow.core.config import Setting
from requests.auth import HTTPBasicAuth
settings = Setting()

import requests 


api_base_url = (
    f"https://api.atlassian.com/ex/jira/"
    f"{settings.JIRA_CLOUD_ID}"
)
ticket_url = (
    f"{api_base_url}/rest/api/3/issue/"
    f"{settings.JIRA_TICKET_KEY}"
)


auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN.get_secret_value())

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

response = requests.get(
    ticket_url,
    headers={"Accept": "application/json"},
    auth=auth,
    timeout=10,
)


data = response.json()



fields = data["fields"]

# print("Key:", data.get("key"))
# print("Summary:", fields.get("summary"))
# print("Priority:", fields.get("priority"))
print("Issue type:", fields.get("issuetype"))
# print("Status:", fields.get("status"))
# print("Labels:", fields.get("labels"))
# print("Description:", fields.get("description"))
