#!/bin/bash

XVFB_WHD=${XVFB_WHD:-1280x720x16}

Xvfb $DISPLAY -ac -screen 0 $XVFB_WHD -nolisten tcp &

exec $@
