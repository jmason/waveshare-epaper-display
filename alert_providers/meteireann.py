from alert_providers.base_provider import BaseAlertProvider
import logging

class MetEireannAlertProvider(BaseAlertProvider):
    '''
    Consume the Met Eireann JSON alert data; format described at
    https://www.met.ie/Open_Data/Warnings/Met_Eireann_Warning_description_June2020.pdf .
    '''

    def __init__(self, feed_url):
        self.feed_url = feed_url

    def get_alert(self):
        alert_data = self.get_response_json(self.feed_url)
        logging.debug("get_alert() - {}".format(alert_data))

        for item in alert_data:
            level = item["level"].capitalize()  	# "yellow" => "Yellow"
            # add the level to the description to make something like
            # "Yellow: "Heavy showers will affect all areas overnight and
            # tomorrow. Expect local flooding"
            value = "%s: %s" % (level, item["description"])
            return value

        return ""
