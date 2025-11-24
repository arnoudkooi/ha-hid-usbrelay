import logging
import usb.core
import usb.util
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH, Platform.BUTTON]

# Integration can only be set up via config entry
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the USB Relay component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up USB Relay from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    # Update entity areas in the registry before reloading
    ent_reg = er.async_get(hass)
    channel_config = entry.options.get("channels", {})
    
    # Update areas for all entities
    for i in range(1, entry.data.get("relays", 8) + 1):
        channel_settings = channel_config.get(f"channel_{i}", {})
        area_id = channel_settings.get("area_id")
        
        # Update switch entity
        switch_unique_id = f"{entry.entry_id}_switch_{i}"
        switch_entity_id = ent_reg.async_get_entity_id("switch", DOMAIN, switch_unique_id)
        if switch_entity_id:
            ent_reg.async_update_entity(switch_entity_id, area_id=area_id)
        
        # Update button entity
        button_unique_id = f"{entry.entry_id}_button_pulse_{i}"
        button_entity_id = ent_reg.async_get_entity_id("button", DOMAIN, button_unique_id)
        if button_entity_id:
            ent_reg.async_update_entity(button_entity_id, area_id=area_id)
    
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
