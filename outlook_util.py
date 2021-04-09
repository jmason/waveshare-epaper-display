import sys
import json
import logging
import datetime
import requests
import msal
import atexit
import os
import time
from datetime import timezone
from utility import configure_logging

configure_logging()


def get_access_token():
    mscache = msal.SerializableTokenCache()
    if os.path.exists("outlooktoken.bin"):
        mscache.deserialize(open("outlooktoken.bin", "r").read())

    atexit.register(lambda:
                    open("outlooktoken.bin", "w").write(mscache.serialize())
                    if mscache.has_state_changed else None
                    )

    app = msal.PublicClientApplication("3b49f0d7-201a-4b5d-b2b4-8f4c3e6c8a30",
                                       authority="https://login.microsoftonline.com/consumers",
                                       token_cache=mscache)

    result = None

    accounts = app.get_accounts()

    if accounts:
        chosen = accounts[0]
        result = app.acquire_token_silent(["https://graph.microsoft.com/Calendars.Read"], account=chosen)

    if not result:
        logging.info("No token exists in cache, login is required.")

        flow = app.initiate_device_flow(scopes=["https://graph.microsoft.com/Calendars.Read"])
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

        print("")
        print(flow["message"])
        sys.stdout.flush()

        result = app.acquire_token_by_device_flow(flow)

    logging.debug(result)

    if "access_token" in result:
        return result["access_token"]
    else:
        logging.error(result.get("error"))
        logging.error(result.get("error_description"))
        logging.error(result.get("correlation_id"))
        raise Exception(result.get("error"))


def get_outlook_calendar_events(calendar_id, from_date, to_date, access_token):
    headers = {'Authorization': 'Bearer ' + access_token}
    endpoint_calendar_view = "https://graph.microsoft.com/v1.0/me/calendars/{0}/calendarview?startdatetime={1}&enddatetime={2}&$orderby=start/dateTime&$top=5"
    events_data = requests.get(
                                endpoint_calendar_view.format(calendar_id, requests.utils.quote(from_date), requests.utils.quote(to_date)),
                                headers=headers).json()
    return events_data


def outlook_utc_to_local_time(utc):
    # Outlook Calendar View returns a specific datetime format (it's valid ISO but Python doesn't pick it up)
    # Outlook Calendar View 'start' is always in UTC.  According to the docs.  In Apr 2021.
    utcdate = datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%S.0000000")
    return utcdate.replace(tzinfo=timezone.utc).astimezone(tz=None).timetuple()


def get_outlook_datetime_formatted(event):
    event_start = event["start"]
    if event['isAllDay'] == True:
        start = event_start.get('dateTime')
        day = time.strftime("%a %b %-d", outlook_utc_to_local_time(start))
    else:
        start = event_start.get('dateTime')
        day = time.strftime("%a %b %-d, %-I:%M %p", outlook_utc_to_local_time(start))

    return day


def main():

    access_token = get_access_token()

    endpoint_calendar_list = "https://graph.microsoft.com/v1.0/me/calendars"

    if access_token:

        headers = {'Authorization': 'Bearer ' + access_token}

        calendars_data = requests.get(endpoint_calendar_list, headers=headers).json()

        print("")
        print("Here are the available Calendar names and IDs.  Copy the ID of the Calendar you want into env.sh")
        for cal in calendars_data["value"]:
            print("============================================")
            print("Name               : ", cal["name"])
            print("ID                 : ", cal["id"])
            print("Any upcoming events: ")
            now_iso = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
            oneyearlater_iso = (datetime.datetime.now().astimezone() + datetime.timedelta(days=365)).astimezone().isoformat()
            logging.debug(now_iso)
            logging.debug(oneyearlater_iso)
            events_data = get_outlook_calendar_events(cal["id"], now_iso, oneyearlater_iso, access_token)

            for event in events_data["value"]:
                print("     ", event["subject"], ": ", event["start"]["dateTime"])
            print("============================================")


if __name__ == "__main__":
    main()
