import requests
import json
import re
import time
from bs4 import BeautifulSoup

class TempMaili:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://tempmaili.com"
        self.csrf_token = None
        self.email = None

    def fetch_csrf_token(self):
        """fetches the csrf token from the tempmaili homepage."""
        try:
            r = self.session.get(self.base_url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            meta = soup.find("meta", {"name": "csrf-token"})
            if meta:
                self.csrf_token = meta["content"]
            else:
                print("[TempMaili] warning: csrf token for tempmaili not found in meta tag.")
        except requests.exceptions.RequestException as e:
            print(f"[TempMaili] error fetching tempmaili csrf token: {e}")
            self.csrf_token = None

    def get_headers(self):
        """returns standard headers for tempmaili requests."""
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,id;q=0.8",
            "content-type": "application/json",
            "origin": self.base_url,
            "priority": "u=1, i",
            "referer": f"{self.base_url}/",
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        xsrf_token_cookie = self.session.cookies.get("XSRF-TOKEN")
        if xsrf_token_cookie:
            headers["x-xsrf-token"] = xsrf_token_cookie
        return headers

    def get_email(self):
        """requests and returns a new temporary email address."""
        self.fetch_csrf_token()
        if not self.csrf_token:
            print("[TempMaili] failed to get tempmaili csrf token. cannot get email.")
            return None
            
        payload = {"_token": self.csrf_token}
        try:
            r = self.session.post(f"{self.base_url}/get_messages", json=payload, headers=self.get_headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            self.email = data.get("mailbox")
            if not self.email and data.get("messages"):
                 if data['messages']:
                     self.email = data['messages'][0]['to']
            if self.email:
                print(f"[TempMaili] temporary email: {self.email}")
            return self.email
        except requests.exceptions.RequestException as e:
            print(f"[TempMaili] error getting email from tempmaili: {e}")
            return None
        except json.JSONDecodeError:
            print("[TempMaili] response from get_messages is not valid json.")
            return None

    def wait_for_message(self, timeout=180, poll_interval=3):
        """
        waits for a message in the tempmaili inbox and extracts the verification code.
        """
        start = time.time()
        payload = {"_token": self.csrf_token} 
        print(f"[TempMaili] waiting for verification code in tempmaili mailbox for {timeout} seconds, checking every {poll_interval} seconds...")
        
        code_regex = r"(\b\d{6}\b)" 

        while time.time() - start < timeout:
            try:
                r = self.session.post(f"{self.base_url}/get_messages", json=payload, headers=self.get_headers(), timeout=10)
                r.raise_for_status()
                data = r.json()
                
                messages = data.get("messages", [])
                if messages:
                    for msg in messages:
                        subject = msg.get("subject", "")
                        html_content = msg.get("html", "")

                        match = re.search(code_regex, subject)
                        if match:
                            return match.group(1)
                        
                        if html_content:
                            match = re.search(code_regex, html_content)
                            if match:
                                return match.group(1)
                
                time.sleep(poll_interval)
            except requests.exceptions.RequestException as e:
                print(f"[TempMaili] error checking tempmaili messages: {e}. retrying...")
                time.sleep(poll_interval)
            except json.JSONDecodeError:
                print("[TempMaili] get_messages response is not valid json. retrying...")
                time.sleep(poll_interval)

        print("[TempMaili] timeout reached. no verification code received from tempmaili.")
        return None