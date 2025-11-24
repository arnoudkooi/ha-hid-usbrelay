import logging
import usb.core
import usb.util
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VID = 0x16C0
PID = 0x05DF

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the USB Relay switches."""
    config_data = hass.data[DOMAIN][entry.entry_id]
    num_relays = config_data.get("relays", 8)
    product_name = config_data.get("product", "USB Relay")
    
    # Get channel configuration from options
    channel_config = entry.options.get("channels", {})

    relays = []
    for i in range(1, num_relays + 1):
        channel_settings = channel_config.get(f"channel_{i}", {})
        relays.append(USBRelaySwitch(
            i, 
            product_name, 
            entry.entry_id,
            channel_settings
        ))

    async_add_entities(relays)

class USBRelaySwitch(SwitchEntity):
    """Representation of a USB Relay switch."""
    
    _attr_should_poll = False
    _attr_assumed_state = False

    def __init__(self, channel, product_name, entry_id, channel_settings=None):
        self._channel = channel
        self._product_name = product_name
        self._entry_id = entry_id
        self._channel_settings = channel_settings or {}
        self._attr_is_on = False
        
        self._attr_has_entity_name = True
        # Use custom name if provided, otherwise default to "Relay {channel}"
        self._attr_name = self._channel_settings.get("name", f"Relay {channel}")
        
        self._attr_unique_id = f"{entry_id}_switch_{channel}"

    @property
    def icon(self):
        """Return icon reflecting current state."""
        return "mdi:toggle-switch-variant" if self.is_on else "mdi:toggle-switch-variant-off"

    @property
    def device_class(self):
        """Return None to prevent default switch behavior."""
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._product_name,
            manufacturer="arnoudkooi.com",
            model=self._product_name,
        )

    async def _send_command(self, cmd):
        """Send command to the relay."""
        result = await self.hass.async_add_executor_job(self._send_command_sync, cmd)
        return result

    def _send_command_sync(self, cmd):
        dev = usb.core.find(idVendor=VID, idProduct=PID)
        if dev is None:
            _LOGGER.error("USB Relay not found")
            return False

        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except:
            pass

        payload = [cmd, self._channel, 0, 0, 0, 0, 0, 0]
        
        try:
            dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, payload)
            return True
        except:
            try:
                 dev.ctrl_transfer(0x21, 0x09, 0x0300, 0, payload)
                 return True
            except Exception as e:
                _LOGGER.error(f"Error sending command: {e}")
                return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if await self._send_command(0xFF):
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if await self._send_command(0xFD):
            self._attr_is_on = False
            self.async_write_ha_state()
