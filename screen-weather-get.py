#!/usr/bin/python

import datetime
import sys
import os
import logging
from weather_providers import climacell, openweathermap, metofficedatahub, metno, accuweather
from utility import update_svg, configure_logging
import textwrap

configure_logging()


def format_weather_description(weather_description):
    if len(weather_description) < 20:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(weather_description, 20, break_long_words=False,
                           max_lines=2, placeholder='...').split('\n')
    weather_dict = {1: splits[0]}
    weather_dict[2] = splits[1] if len(splits) > 1 else ''
    return weather_dict


def main():

    # gather relevant environment configs
    climacell_apikey = os.getenv("CLIMACELL_APIKEY")
    openweathermap_apikey = os.getenv("OPENWEATHERMAP_APIKEY")
    metoffice_clientid = os.getenv("METOFFICEDATAHUB_CLIENT_ID")
    metoffice_clientsecret = os.getenv("METOFFICEDATAHUB_CLIENT_SECRET")
    accuweather_apikey = os.getenv("ACCUWEATHER_APIKEY")
    accuweather_locationkey = os.getenv("ACCUWEATHER_LOCATIONKEY")
    metno_self_id = os.getenv("METNO_SELF_IDENTIFICATION")

    location_lat = os.getenv("WEATHER_LATITUDE", "51.3656")
    location_long = os.getenv("WEATHER_LONGITUDE", "-0.1963")

    weather_format = os.getenv("WEATHER_FORMAT", "CELSIUS")

    if (
        not climacell_apikey
        and not openweathermap_apikey
        and not metoffice_clientid
        and not accuweather_apikey
        and not metno_self_id
    ):
        logging.error("No weather provider has been configured (Climacell, OpenWeatherMap, MetOffice, AccuWeather, Met.no...)")
        sys.exit(1)

    if (weather_format == "CELSIUS"):
        units = "metric"
    else:
        units = "imperial"

    if metno_self_id:
        logging.info("Getting weather from Met.no")
        weather_provider = metno.MetNo(metno_self_id, location_lat, location_long, units)

    elif accuweather_apikey:
        logging.info("Getting weather from Accuweather")
        weather_provider = accuweather.AccuWeather(accuweather_apikey, location_lat,
                                                   location_long,
                                                   accuweather_locationkey,
                                                   units)

    elif metoffice_clientid:
        logging.info("Getting weather from Met Office Weather Datahub")
        weather_provider = metofficedatahub.MetOffice(metoffice_clientid,
                                                      metoffice_clientsecret,
                                                      location_lat,
                                                      location_long,
                                                      units)

    elif openweathermap_apikey:
        logging.info("Getting weather from OpenWeatherMap")
        weather_provider = openweathermap.OpenWeatherMap(openweathermap_apikey,
                                                         location_lat,
                                                         location_long,
                                                         units)

    elif climacell_apikey:
        logging.info("Getting weather from Climacell")
        weather_provider = climacell.Climacell(climacell_apikey, location_lat, location_long, units)

    weather = weather_provider.get_weather()
    logging.info("weather - {}".format(weather))

    if not weather:
        logging.error("Unable to fetch weather payload. SVG will not be updated.")
        return

    degrees = "°C" if units == "metric" else "°F"

    weather_desc = format_weather_description(weather["description"])

    output_dict = {
        'LOW': "{}{}".format(str(round(weather['temperatureMin'])), degrees),
        'HIGH': "{}{}".format(str(round(weather['temperatureMax'])), degrees),
        'ICON_ONE': weather["icon"],
        'WEATHER_DESC_1': weather_desc[1],
        'WEATHER_DESC_2': weather_desc[2],
        'TIME_NOW': datetime.datetime.now().strftime("%-I:%M %p"),
        'HOUR_NOW': datetime.datetime.now().strftime("%-I %p"),
        'DAY_ONE': datetime.datetime.now().strftime("%b %-d, %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE': ""  # unused, see: https://github.com/mendhak/waveshare-epaper-display/issues/13
    }

    logging.debug("main() - {}".format(output_dict))

    logging.info("Updating SVG")
    template_svg_filename = 'screen-template.svg'
    output_svg_filename = 'screen-output-weather.svg'
    update_svg(template_svg_filename, output_svg_filename, output_dict)


if __name__ == "__main__":
    main()
