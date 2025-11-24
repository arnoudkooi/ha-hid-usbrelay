import logging
import usb.core
import usb.util
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VID = 0x16C0
PID = 0x05DF

class UsbRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for USB Relay."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            # If user manually inputs something (not really used here but good for structure)
            pass

        # Attempt to find the device automatically
        try:
            device = await self.hass.async_add_executor_job(self._find_device)
            if device:
                await self.async_set_unique_id(f"{VID:04x}:{PID:04x}")
                self._abort_if_unique_id_configured()
                
                product_name = device.get("product", "USB Relay")
                num_relays = device.get("num_relays", 8)

                return self.async_create_entry(
                    title=product_name,
                    data={"relays": num_relays, "product": product_name}
                )
            else:
                errors["base"] = "no_device"
        except Exception as e:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={},
        )

    def _find_device(self):
        """Find the device and return info."""
        dev = usb.core.find(idVendor=VID, idProduct=PID)
        if dev is None:
            return None
        
        # Try to get product string
        try:
            product = usb.util.get_string(dev, dev.iProduct)
        except:
            product = "USBRelay8"
            
        num_relays = 8
        if product:
            if "Relay1" in product: num_relays = 1
            elif "Relay2" in product: num_relays = 2
            elif "Relay4" in product: num_relays = 4
            elif "Relay8" in product: num_relays = 8
            
        return {"product": product, "num_relays": num_relays}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return UsbRelayOptionsFlow(config_entry)


class UsbRelayOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for USB Relay."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Process the input and structure it
            channels = {}
            num_relays = self.config_entry.data.get("relays", 8)
            
            for i in range(1, num_relays + 1):
                channels[f"channel_{i}"] = {
                    "name": user_input.get(f"channel_{i}_name", f"Relay {i}"),
                    "area_id": user_input.get(f"channel_{i}_area", None),
                }
            
            return self.async_create_entry(title="", data={"channels": channels})

        # Build schema with current values
        num_relays = self.config_entry.data.get("relays", 8)
        channel_config = self.config_entry.options.get("channels", {})
        
        schema = {}
        for i in range(1, num_relays + 1):
            current = channel_config.get(f"channel_{i}", {})
            schema[vol.Optional(
                f"channel_{i}_name", 
                default=current.get("name", f"Relay {i}")
            )] = str
            schema[vol.Optional(
                f"channel_{i}_area", 
                default=current.get("area_id", None)
            )] = selector.AreaSelector()
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            description_placeholders={"num_relays": str(num_relays)},
        )

