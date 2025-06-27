from core.tempmail_service import TempMaili
from core.instagram_api import InstagramAPI
from core.crypto_utils import InstagramCrypto
from utils.helpers import generate_random_birthdate
import time
import json
import random

def run_registration_process(password):
    mail_service = TempMaili()
    ig_api = InstagramAPI()

    temp_email_generated = mail_service.get_email()
    if not temp_email_generated:
        return "failed_temp_email"

    initial_ig_csrftoken, initial_ig_jazoest, client_id_from_cookie = ig_api.get_initial_ig_data()
    if not initial_ig_csrftoken or not initial_ig_jazoest:
        return "failed_initial_data"

    client_id_for_payload = client_id_from_cookie if client_id_from_cookie else "aFzllgAEAAE6YP0KL8pqhSBjzfg5"

    ig_encryption_config = ig_api.get_ig_encryption_config()
    if not ig_encryption_config:
        return "failed_encryption_config"

    ig_crypto = InstagramCrypto(ig_encryption_config)

    dynamic_enc_password = ig_crypto.encrypt_password(password)
    if not dynamic_enc_password:
        return "failed_encrypt_password"

    ig_api.set_base_headers(initial_ig_csrftoken)
    first_attempt_payload = {
        "email": temp_email_generated,
        "first_name": "",
        "username": "",
        "opt_into_one_tap": "false",
        "use_new_suggested_user_name": "true",
        "jazoest": initial_ig_jazoest
    }
    response_first_post = ig_api.post_request(ig_api.IG_POST_ATTEMPT_URL, first_attempt_payload)

    selected_username_from_suggestions = None
    if response_first_post:
        try:
            response_json_first = response_first_post.json()
            username_suggestions = response_json_first.get("username_suggestions")
            if username_suggestions and isinstance(username_suggestions, list) and len(username_suggestions) > 0:
                selected_username_from_suggestions = random.choice(username_suggestions)
                print(f"[Instagram] Random Username: {selected_username_from_suggestions}")
            else:
                return "no_username_suggestions"
        except json.JSONDecodeError:
            return "invalid_json_post_1"
    else:
        return "failed_post_1"
    time.sleep(2)

    random_day, random_month, random_year = generate_random_birthdate(2000, 2002)

    second_attempt_payload = {
        "enc_password": dynamic_enc_password,
        "email": temp_email_generated,
        "first_name": selected_username_from_suggestions,
        "username": selected_username_from_suggestions,
        "client_id": client_id_for_payload,
        "seamless_login_enabled": "1",
        "opt_into_one_tap": "false",
        "use_new_suggested_user_name": "true",
        "jazoest": initial_ig_jazoest,
    }
    response_second_post = ig_api.post_request(ig_api.IG_POST_ATTEMPT_URL, second_attempt_payload)

    if response_second_post:
        try:
            response_json_second = response_second_post.json()
            if response_json_second.get("error_type") == "signup_block" and "ip" in response_json_second.get("errors", {}):
                print("[Instagram] ", response_json_second.get("errors", {}).get("ip", ["Unknown IP error"])[0])
                return "signup_block_ip"
            else:
                if response_json_second.get("errors"):
                    print("[Instagram] Pesan Error:")
                    print(json.dumps(response_json_second["errors"], indent=4))
                    return "failed_account_creation"
        except json.JSONDecodeError:
            return "invalid_json_post_2"
    else:
        return "failed_post_2"
    time.sleep(2)

    print(f"[Instagram] Birthday: {random_day}/{random_month}/{random_year}")
    check_age_payload = {
        "day": random_day,
        "month": random_month,
        "year": random_year,
        "jazoest": initial_ig_jazoest
    }
    response_check_age = ig_api.post_request(ig_api.IG_CHECK_AGE_URL, check_age_payload)
    if not response_check_age:
        return "failed_post_3"
    try:
        response_check_age.json()
    except json.JSONDecodeError:
        return "invalid_json_post_3"
    time.sleep(2)

    send_verify_email_payload = {
        "device_id": client_id_for_payload,
        "email": temp_email_generated,
        "jazoest": initial_ig_jazoest
    }
    print("[Instagram] Send Verify Email")
    response_send_verify_email = ig_api.post_request(ig_api.IG_SEND_VERIFY_EMAIL_URL, send_verify_email_payload)

    verification_code = None
    if response_send_verify_email:
        try:
            response_json_email_sent = response_send_verify_email.json()
            if response_json_email_sent.get("status") == "ok":
                verification_code = mail_service.wait_for_message(timeout=180, poll_interval=3)
                if verification_code:
                    print(f"[TempMaili] Instagram verification code: {verification_code}")
                else:
                    return "failed_email_code_timeout"
            else:
                return "email_send_not_ok"
        except json.JSONDecodeError:
            return "invalid_json_post_4"
    else:
        return "failed_post_4"
    time.sleep(2)

    check_code_payload = {
        "code": verification_code,
        "device_id": client_id_for_payload,
        "email": temp_email_generated,
        "jazoest": initial_ig_jazoest
    }
    print("[Instagram] Check Confirmation Code")
    response_check_code = ig_api.post_request(ig_api.IG_CHECK_CONFIRMATION_CODE_URL, check_code_payload)

    signup_code_from_email_confirm = None
    if response_check_code:
        try:
            response_json_code_checked = response_check_code.json()
            if response_json_code_checked.get("status") == "ok":
                print("[Instagram] Success")
                signup_code_from_email_confirm = response_json_code_checked.get("signup_code")
                if not signup_code_from_email_confirm:
                    return "missing_signup_code"
            else:
                return "failed_email_verification"
        except json.JSONDecodeError:
            return "invalid_json_post_5"
    else:
        return "failed_post_5"
    time.sleep(2)

    print("[Instagram] Create Account")
    final_enc_password_for_step6 = ig_crypto.encrypt_password(password)
    if not final_enc_password_for_step6:
        return "failed_encrypt_password_final_step"

    extra_session_id_for_final_payload = "nlvx0f:c9dn73:d5nr3v"

    final_create_payload = {
        "enc_password": final_enc_password_for_step6,
        "day": random_day,
        "email": temp_email_generated,
        "failed_birthday_year_count": "{}",
        "first_name": selected_username_from_suggestions,
        "month": random_month,
        "username": selected_username_from_suggestions,
        "year": random_year,
        "client_id": client_id_for_payload,
        "seamless_login_enabled": "1",
        "tos_version": "row",
        "force_sign_up_code": signup_code_from_email_confirm,
        "extra_session_id": extra_session_id_for_final_payload,
        "jazoest": initial_ig_jazoest,
    }

    response_final_create = ig_api.post_request(ig_api.IG_FINAL_CREATE_URL, final_create_payload)

    if response_final_create:
        try:
            final_response_json = response_final_create.json()
            if final_response_json.get("account_created") == True:
                print("[Instagram] Success")
                return "success"
            else:
                if final_response_json.get("error_type") == "signup_block" and "ip" in final_response_json.get("errors", {}):
                    print("[Instagram] Error Message: ", final_response_json.get("errors", {}).get("ip", ["Unknown IP error"])[0])
                    return "ip_block_error"
                else:
                    print("[Instagram] Failed to Create Account")
                    print(json.dumps(final_response_json.get("errors", {}), indent=4))
                    return "final_account_creation_failed"
        except json.JSONDecodeError:
            return "invalid_json_post_6"
    else:
        return "failed_post_6"

if __name__ == "__main__":
    print("""
.___  _______________________.___.
|   |/  _____/\\______   \\__  |   |
|   /   \\  ___ |     ___//   |   |
|   \\    \\_\\  \\|    |    \\____   |
|___|\\______  /|____|    / ______|
            \\/           \\/                     
    """)
    my_desired_password = "AkunInstagram123"
    result = run_registration_process(my_desired_password)

    if result == "success":
        print("[Script] Success Create Instagram Account")
    elif result == "ip_block_error":
        print("[Script] Ip Block")
    else:
        print(f"[Script] Error: {result}")
