import requests

import os
from dotenv import load_dotenv

load_dotenv()


personal_token = os.getenv("PERSONAL_TOKEN")
        # print(self.personal_token)
headers = {"Authorization": "token " + personal_token}

# 有问题的patch
patch_url = "https://github.com/MicrosoftDocs/azure-docs/commit/101df12c4b6f4e6a9b98488dac4c45504a8032e9.patch"

# ok的patch
patch_url = "https://github.com/MicrosoftDocs/azure-docs/commit/4c7354d3a2b654355601d751db3691687c72acb5.patch"

try:
    response = requests.get(patch_url, stream=True, headers=headers)
    response.raise_for_status()
    response_raw_text = response.text
    print(response_raw_text)
except requests.exceptions.HTTPError as errh:
    print("HTTP Error:", errh)
except requests.exceptions.ConnectionError as errc:
    print("Error Connecting:", errc)
except requests.exceptions.Timeout as errt:
    print("Timeout Error:", errt)
except requests.exceptions.RequestException as err:
    print("Something went wrong:", err)
except Exception as e:
    print("Unknown Exception:", e)


print(response_raw_text)



