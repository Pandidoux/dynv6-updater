import requests
import time
import json
import logging

verbose = False
zone = "zone"  # Zone to update
token = "token"  # Your zone token
update_period = 60  # Update every 10 minutes (adjust as needed)
update_type = "both"  # IP type to update "both" / "ipv4only" / "ipv6only"
ip_file = "ip.json"  # File to store the last recorded IP addresses


# Configure logging
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG if verbose else logging.INFO,
)


def get_ip_addresses():
    # Get ip addresses API URL
    api_v4_url = "https://v4.ident.me"  # alternative: "https://api.ipify.org"
    api_v6_url = "https://v6.ident.me"  # alternative: "https://api64.ipify.org"
    ip_addresses = {}
    if update_type == "both":  # Get both ipv4 and ipv6
        ip_addresses["ipv4"] = requests.get(api_v4_url).text
        ip_addresses["ipv6"] = requests.get(api_v6_url).text
    elif update_type == "ipv4only":  # Get ipv4 only
        ip_addresses["ipv4"] = requests.get(api_v4_url).text
        ip_addresses["ipv6"] = "6to4"  # https://dynv6.com/docs/apis
    elif update_type == "ipv6only":  # Get ipv6 only
        ip_addresses["ipv4"] = "auto"  # https://dynv6.com/docs/apis
        ip_addresses["ipv6"] = requests.get(api_v6_url).text
    else:
        logging.error("Unsupported update_type value.")
        exit(1)
    if verbose:
        logging.info("Actual IPv4: " + ip_addresses["ipv4"])
        logging.info("Actual IPv6: " + ip_addresses["ipv6"])
    return ip_addresses


def has_ip_changed(ip_addresses):
    try:
        with open(ip_file, "r") as file:
            saved_ip_addresses = json.load(file)
        if update_type == "both":  # Get both ipv4 and ipv6
            ipv4_changed = ip_addresses["ipv4"] != saved_ip_addresses["ipv4"]
            ipv6_changed = ip_addresses["ipv6"] != saved_ip_addresses["ipv6"]
            return ipv4_changed or ipv6_changed
        elif update_type == "ipv4only":  # Get ipv4 only
            return ip_addresses["ipv4"] != saved_ip_addresses["ipv4"]
        elif update_type == "ipv6only":  # Get ipv6 only
            return ip_addresses["ipv6"] != saved_ip_addresses["ipv6"]
        else:
            logging.error("Unsupported update_type value.")
            exit(1)
    except FileNotFoundError:
        if verbose:
            logging.info("Write " + ip_file + " file to store previous IP addresses.")
        try:  # Write previous IP file
            with open(ip_file, "w") as file:
                json.dump(ip_addresses, file)
        except Exception as e:
            logging.error(f"Failed to write {ip_file}: {str(e)}")
            exit(1)
        return True  # Consider IP has changed to update for the first time


def update_ip_addresses(ip_addresses):
    dynv6_api_url = "http://dynv6.com/api/update"
    full_ipv4_url = str(dynv6_api_url) + "?hostname=" + str(zone) + "&token=" + str(token) + "&ipv4=" + str(ip_addresses["ipv4"])
    full_ipv6_url = str(dynv6_api_url) + "?hostname=" + str(zone) + "&token=" + str(token) + "&ipv6prefix=" + str(ip_addresses["ipv6"])
    if update_type == "both":  # Get both ipv4 and ipv6
        response = requests.get(full_ipv4_url)
        response = requests.get(full_ipv6_url)
    elif update_type == "ipv4only":  # Get ipv4 only
        response = requests.get(full_ipv4_url)
    elif update_type == "ipv6only":  # Get ipv6 only
        response = requests.get(full_ipv6_url)
    else:
        logging.error("Unsupported update_type value.")
        exit(1)
    if response.status_code == 200:
        logging.info("Status: " + str(response.status_code))
    else:
        logging.warning("Status: " + str(response.status_code))
    logging.info("Response: " + response.text)
    logging.info("IP addresses update done.")
    try:  # Write previous IP file
        with open(ip_file, "w") as file:
            json.dump(ip_addresses, file)
    except Exception as e:
        logging.error(f"Failed to write {ip_file}: {str(e)}")
        exit(1)


def main():
    while True:
        current_ip_addresses = get_ip_addresses()
        if has_ip_changed(current_ip_addresses):
            update_ip_addresses(current_ip_addresses)
        else:
            logging.info("No IP address change.")
        time.sleep(update_period * 60)  # Sleep for update_period minutes


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Manual keyboard interruption detected. Stop update")
        exit(0)
