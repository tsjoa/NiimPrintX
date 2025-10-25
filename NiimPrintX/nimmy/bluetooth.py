from __future__ import annotations

import asyncio
import platform
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bleak import BleakClient, BleakScanner
from loguru import logger

from .exception import BLEException
from .logger_config import get_logger

if platform.system() == "Linux":
    from bluepy.btle import Peripheral, BTLEDisconnectError

if TYPE_CHECKING:
    from bleak import BleakClient, BLEDevice

SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
P15_MAC_ADDRESS = "03:0D:7A:D6:5E:B1"


class BluetoothPrinter(ABC):
    """Abstract base class for Bluetooth printer interactions."""

    @abstractmethod
    async def connect(self) -> None:
        """Connects to the Bluetooth printer."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnects from the Bluetooth printer."""
        raise NotImplementedError

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """Writes data to the Bluetooth printer."""
        raise NotImplementedError


if platform.system() == "Linux":

    class BluepyBluetoothPrinter(BluetoothPrinter):
        """BluetoothPrinter implementation using bluepy library for Linux."""

        def __init__(self, device_address: str):
            self.device_address = device_address
            self.peripheral: Peripheral | None = None
            self.characteristic = None

        async def connect(self) -> None:
            """Connects to the Bluetooth printer using bluepy."""
            retries = 5
            delay = 2
            for i in range(retries):
                try:
                    logger.info(f"Connecting to {self.device_address} (attempt {i+1}/{retries})...")
                    self.peripheral = Peripheral(self.device_address)
                    self.peripheral.setMTU(100)
                    self.characteristic = self.peripheral.getCharacteristics(uuid=CHAR_UUID)[0]
                    logger.info(f"Connected to {self.device_address}")
                    await asyncio.sleep(0.5) # Add a small delay after connection
                    return
                except BTLEDisconnectError as e:
                    logger.warning(f"Connection attempt {i+1}/{retries} failed: {e}")
                    if i < retries - 1:
                        await asyncio.sleep(delay)
                    else:
                        logger.error("Could not connect. Make sure the printer is in BLE mode (blue light).")
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error during bluepy connection: {e}")
                    await asyncio.sleep(delay)
            raise ConnectionError("Failed to connect to printer using bluepy.")

        async def disconnect(self) -> None:
            """Disconnects from the Bluetooth printer."""
            if self.peripheral:
                try:
                    self.peripheral.disconnect()
                    logger.info("Disconnected from printer.")
                except Exception as e:
                    logger.error(f"Error during bluepy disconnect: {e}")
                finally:
                    self.peripheral = None
                    self.characteristic = None

        async def write(self, data: bytes) -> None:
            """Writes data to the Bluetooth printer using bluepy."""
            if not self.characteristic:
                raise ConnectionError("Not connected to printer.")
            try:
                self.characteristic.write(data, withResponse=False)
            except Exception as e:
                logger.error(f"Error writing data with bluepy: {e}")
                raise


async def find_device(device_name_prefix=None) -> BLEDevice:
    devices = await BleakScanner.discover()
    if device_name_prefix == "p15":
        for device in devices:
            if device.address == P15_MAC_ADDRESS:
                return device
        raise BLEException(f"Failed to find P15 device at {P15_MAC_ADDRESS}")
    else:
        for device in devices:
            if device.name and device.name.lower().startswith(device_name_prefix.lower()):
                return device
        raise BLEException(f"Failed to find device {device_name_prefix}")


async def scan_devices(device_name=None):
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        if device_name:
            if device.name and device_name.lower() in device.name.lower():
                print(f"Found device: {device.name} at {device.address}")
                return device
        else:
            print(f"Found device: {device.name} at {device.address}")
    return None


class BLETransport:
    def __init__(self, address=None):
        self.address = address
        self.client = None

    async def __aenter__(self):
        # Automatically connect if address is provided during initialization
        if self.address:
            self.client = BleakClient(self.address)
            if await self.client.connect():
                logger.info(f"Connected to {self.address}")
                return self
            else:
                raise BLEException(f"Failed to connect to the BLE device at {self.address}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected.")

    async def connect(self, address):
        if self.client is None:
            self.client = BleakClient(address)
        if not self.client.is_connected:
            return await self.client.connect()
        return False

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def write(self, data, char_uuid):
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(char_uuid, data)
        else:
            raise BLEException("BLE client is not connected.")

    async def start_notification(self, char_uuid, handler):
        if self.client and self.client.is_connected:
            await self.client.start_notify(char_uuid, handler)
        else:
            raise BLEException("BLE client is not connected.")

    async def stop_notification(self, char_uuid):
        if self.client and self.client.is_connected:
            await self.client.stop_notify(char_uuid)
        else:
            raise BLEException("BLE client is not connected.")
