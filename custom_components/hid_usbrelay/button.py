import logging
import time
import usb.core
import usb.util
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VID = 0x16C0
PID = 0x05DF

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the USB Relay buttons."""
    config_data = hass.data[DOMAIN][entry.entry_id]
    num_relays = config_data.get("relays", 8)
    product_name = config_data.get("product", "USB Relay")
    
    # Get channel configuration from options
    channel_config = entry.options.get("channels", {})

    buttons = []
    for i in range(1, num_relays + 1):
        channel_settings = channel_config.get(f"channel_{i}", {})
        buttons.append(USBRelayPulseButton(
            i, 
            product_name, 
            entry.entry_id,
            channel_settings
        ))

    async_add_entities(buttons)

class USBRelayPulseButton(ButtonEntity):
    """Representation of a USB Relay Pulse Button."""

    def __init__(self, channel, product_name, entry_id, channel_settings=None):
        self._channel = channel
        self._product_name = product_name
        self._entry_id = entry_id
        self._channel_settings = channel_settings or {}
        
        self._attr_has_entity_name = True
        # Use custom name if provided with "Pulse" suffix, otherwise default to "Relay {channel} Pulse"
        custom_name = self._channel_settings.get("name", f"Relay {channel}")
        self._attr_name = f"{custom_name} Pulse"
        
        self._attr_unique_id = f"{entry_id}_button_pulse_{channel}"
        self._attr_icon = "mdi:electric-switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._product_name,
            manufacturer="arnoudkooi.com",
            model=self._product_name,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        # Perform the pulse
        await self.hass.async_add_executor_job(self._pulse_sync)
        
        # After pulse completes, find and update the corresponding switch entity
        registry = er.async_get(self.hass)
        switch_unique_id = f"{self._entry_id}_switch_{self._channel}"
        switch_entity_id = registry.async_get_entity_id("switch", DOMAIN, switch_unique_id)
        
        if switch_entity_id:
            # Get the actual switch entity object
            switch_entity = self.hass.data["entity_components"]["switch"].get_entity(switch_entity_id)
            if switch_entity:
                # Update the switch to reflect OFF state after pulse
                switch_entity._attr_is_on = False
                switch_entity.async_write_ha_state()

    def _pulse_sync(self):
        """Perform the pulse synchronously."""
        dev = usb.core.find(idVendor=VID, idProduct=PID)
        if dev is None:
            _LOGGER.error("USB Relay not found for pulse")
            return

        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except:
            pass

        # Turn OFF first to ensure clean state if it was already ON
        try:
            self._write_cmd(dev, 0xFD) 
            time.sleep(0.1) # Small delay to ensure relay settles
        except:
            pass

        # Pulse: ON -> Wait -> OFF
        try:
            self._write_cmd(dev, 0xFF)
            time.sleep(1.0) # 1 second pulse
            self._write_cmd(dev, 0xFD)
        except Exception as e:
            _LOGGER.error(f"Pulse failed: {e}")

    def _write_cmd(self, dev, cmd):
        payload = [cmd, self._channel, 0, 0, 0, 0, 0, 0]
        try:
            dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, payload)
        except:
            dev.ctrl_transfer(0x21, 0x09, 0x0300, 0, payload)
