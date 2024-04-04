
. env.sh

function log {
    echo "---------------------------------------"
    echo ${1^^}
    echo "---------------------------------------"
}

if [ $WAVESHARE_EPD75_VERSION = 1 ]; then
    export WAVESHARE_WIDTH=640
    export WAVESHARE_HEIGHT=384
else
    export WAVESHARE_WIDTH=800
    export WAVESHARE_HEIGHT=480
fi

if [ $PRIVACY_MODE = 1 ]; then
    log "Get XKCD comic strip"
    .venv/bin/python3 xkcd_get.py
    if [ $? -eq 0 ]; then
        .venv/bin/python3 display.py xkcd-comic-strip.png
    fi

else

    log "Add weather info"
    .venv/bin/python3 screen-weather-get.py

    log "Add Calendar info"
    .venv/bin/python3 screen-calendar-get.py

    # Only layout 5 shows a calendar, so save a few seconds.
    if [ "$SCREEN_LAYOUT" -eq 5 ]; then
        log "Add Calendar month"
        .venv/bin/python3 screen-calendar-month.py
    fi

    if [ -f screen-custom-get.py ]; then
        log "Add Custom data"
        .venv/bin/python3 screen-custom-get.py
    elif [ ! -f screen-output-custom-temp.svg ]; then
        # Create temporary empty svg since the main SVG needs it
        echo "<svg />" > screen-output-custom-temp.svg
    fi


    log "Export to PNG"

    inkscape screen-output-weather.svg --without-gui -e screen-output.png -w$WAVESHARE_WIDTH -h$WAVESHARE_HEIGHT --export-dpi=300


    .venv/bin/python3 display.py screen-output.png
fi
