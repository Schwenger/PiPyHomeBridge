# General
* Fix white temperatures and colors/brightness.
* Remote does not have one universal target; separate targets for different actions.

# UI
* Each abstract light in the app has a checkbox to define its parameters or inherit
  * This sets its full config or removes it.
* Separate control and configuration/re-structuring

# Groups
* Combine home.flatten_lights and home.compile_config.
* Base everything on groups
  * In App when displaying a room, offer option to control lights as a whole
  * Option to jump into a group, same thing
  * Offer option to jump into list of devices as secondary option
* Room cannot be targeted by remote actions; use groups instead, that's what they are for...

# Overrides
* Wrap modifier in config in override, too.
  * When dimming, set temporary override
  * When configuring, set permanent override
    * Rename functions accordingly.
    * Also add API commands.