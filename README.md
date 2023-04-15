# PiPyHomeBridge
A simple little smart home base.

The base is intended to be run on a Raspberry Pi. It operates as an MQTT-client using the [eclipse paho](https://www.eclipse.org/paho/) library to sends commands to an MQTT server. There, commands are translated into zigbee commands (e.g. with [MQTT2Zigbee](https://www.zigbee2mqtt.io)) and executed on smart home devices.

Internally, the application spawn four threads.
* The WebAPI accepts web requests to be controlled from the outside, e.g. with my companion iOS-App [MSh]().  It parses requests and pushes them into an internal queue to be executed via the API.
* The API as a counter-part to the WebAPI.  It receives querys or commands from the queue and executes them.
* The Controller, which receives messages from the MQTT Server, parses them and when necessary pushes them into the queue.
* The Refresher, regularly refreshing all lights to keep them appropriate for the current time of day.

The whole project is a tiny python-training-exercise gone wild.  Before starting, I barely had experience with python and it shows.  Yet, I learned quite a bit and it was immensely fun.  Since the project was not supposed to grow, I never wrote tests, so the whole thing is fragile.  I might re-write it at some point, possibly in Rust. For now, it works, tho.

# Authors
* Maximilian Schwenger

# Lizence
I hereby grant you full access to the code without any restrictions.  Go nuts, redistribute it commercially and go bankrupt because of it, tattoo it on your black claiming it's your own, submit it as your Bachelor Thesis and fail spectacularly, do whatever.  Just don't hold me responsible.

# Documentation
I sometimes used comprehensible names.  Should suffice.