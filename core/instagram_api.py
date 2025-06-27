import requests
import re
import json
import time

class InstagramAPI:
    IG_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
    IG_POST_ATTEMPT_URL = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
    IG_CHECK_AGE_URL = "https://www.instagram.com/api/v1/web/consent/check_age_eligibility/"
    IG_SEND_VERIFY_EMAIL_URL = "https://www.instagram.com/api/v1/accounts/send_verify_email/"
    IG_CHECK_CONFIRMATION_CODE_URL = "https://www.instagram.com/api/v1/accounts/check_confirmation_code/"
    IG_FINAL_CREATE_URL = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"

    def __init__(self):
        self.session = requests.Session()
        self.base_headers = {}

    def set_base_headers(self, csrftoken):
        """sets base headers to be used for all instagram requests."""
        self.base_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,id;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.instagram.com",
            "priority": "u=1, i",
            "referer": "https://www.instagram.com/accounts/emailsignup/",
            "sec-ch-prefers-color-scheme": "dark",
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v=\"24"',
            "sec-ch-ua-full-version-list": '"Chromium";v="137.0.7151.103", "Not/A)Brand";v="24.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Linux"',
            "sec-ch-ua-platform-version": '"6.14.11"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "x-asbd-id": "359341",
            "x-csrftoken": csrftoken,
            "x-ig-app-id": "936619943392459",
            "x-ig-www-claim": "0",
            "x-instagram-ajax": "1024218542",
            "x-requested-with": "XMLHttpRequest",
            "x-web-session-id": "bzljtk:hkmimh:aamjfb"
        }

    def get_initial_ig_data(self):
        """accesses the instagram signup page to get cookies and jazoest."""
        try:
            response_get = self.session.get(self.IG_SIGNUP_URL, timeout=10)
            response_get.raise_for_status()

            csrftoken = self.session.cookies.get('csrftoken')
            mid_cookie = self.session.cookies.get('mid') 
            
            if not csrftoken:
                return None, None, None

            jazoest_match = re.search(r'jazoest=(\d+)', response_get.text)
            jazoest_value = jazoest_match.group(1) if jazoest_match else None
            if not jazoest_value:
                return csrftoken, None, mid_cookie
            
            return csrftoken, jazoest_value, mid_cookie

        except requests.exceptions.RequestException as e:
            print(f"[Instagram] error performing get request: {e}")
            return None, None, None

    def get_ig_encryption_config(self):
        """fetches encryption configuration from /data/shared_data/."""
        try:
            shared_data_response = self.session.get("https://www.instagram.com/data/shared_data/", timeout=10)
            shared_data_response.raise_for_status()
            shared_data_json = shared_data_response.json()
            encryption_config = shared_data_json.get("encryption")
            
            if not encryption_config:
                return None
            
            return encryption_config

        except requests.exceptions.RequestException as e:
            print(f"[Instagram] error fetching encryption config: {e}")
            return None
        except json.JSONDecodeError:
            print("[Instagram] shared_data response is not valid json.")
            return None

    def post_request(self, url, payload):
        """performs a generic post request to an instagram url."""
        try:
            response = self.session.post(url, headers=self.base_headers, data=payload, timeout=15)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"[Instagram] post request to {url} failed: {e}")
            return None
        except Exception as e:
            print(f"[Instagram] unexpected error performing post request to {url}: {e}")
            return None