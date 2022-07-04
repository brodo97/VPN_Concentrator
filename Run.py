import os
import requests as req
from Config import *
import netifaces as ni
import subprocess
import time


TELEGRAM_URI = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/"


def start_vpn(session, message_id: int):
    try:
        ip = ni.ifaddresses('tun0')[ni.AF_INET][0]['addr']

        text = f"VPN already ON.\nIP: {ip}"

        session.get(
            TELEGRAM_URI + f"sendMessage?chat_id={BOT_ADMIN_ID}&text={text}&reply_to_message_id={message_id}"
        )
        return
    except Exception:
        pass

    proc = subprocess.Popen(
        ["systemctl", "start", f"openvpn@{WHO_AM_I}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    ip = None

    for _ in range(15):
        time.sleep(1)
        try:
            ip = ni.ifaddresses('tun0')[ni.AF_INET][0]['addr']
            break
        except Exception:
            pass

    if ip is None:
        text = "Error while starting VPN"
    else:
        text = f"VPN now ON.\nIP: {ip}"

    session.get(
        TELEGRAM_URI + f"sendMessage?chat_id={BOT_ADMIN_ID}&text={text}&reply_to_message_id={message_id}"
    )


def stop_vpn(session, message_id: int):
    proc = subprocess.Popen(
        ["systemctl", "stop", f"openvpn@{WHO_AM_I}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    text = "VPN OFF."
    session.get(
        TELEGRAM_URI + f"sendMessage?chat_id={BOT_ADMIN_ID}&text={text}&reply_to_message_id={message_id}"
    )


def update_messages(session, last_update_id: int = None):
    offset = f"?offset={last_update_id}" if last_update_id is not None else ""

    response = session.get(
        TELEGRAM_URI + "getUpdates" + offset
    )

    if response.status_code != 200:
        exit()

    response = response.json()

    if response["ok"] is not True:
        exit()

    with open("LastUpdateID", "w") as _F:
        _F.write(str(response["result"][-1]["update_id"]))

    for message in response["result"]:
        if message["message"]["chat"]["id"] != BOT_ADMIN_ID or message["update_id"] == last_update_id:
            continue

        text = message["message"]["text"]

        if WHO_AM_I not in text:
            continue

        if text.startswith("/vpnon"):
            start_vpn(session, message["message"]["message_id"])

        elif text.startswith("/vpnoff"):
            stop_vpn(session, message["message"]["message_id"])


if __name__ == "__main__":
    SESSION = req.Session()

    if os.path.exists("LastUpdateID"):
        with open("LastUpdateID") as _F:
            update_id = int(_F.read().strip())
        update_messages(SESSION, update_id)
    else:
        update_messages(SESSION)

