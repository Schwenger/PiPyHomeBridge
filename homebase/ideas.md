* is_dimmable and is_color as property rather than function
* is_dimmable and is_color can be infered from model, same in swift.
* Each abstract light in the app has a checkbox to define its parameters or inherit
  * This sets its full config or removes it.
* Fix white temperatures.
* Wrap modifier in config in override, too.
  * When dimming, set temporary override
  * When configuring, set permanent override
    * Rename functions accordingly.
    * Also add API commands.
* Combine home.flatten_lights and home.compile_config.