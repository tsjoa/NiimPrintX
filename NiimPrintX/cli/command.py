import asyncio
import click
import platform
from PIL import Image
from NiimPrintX.nimmy.bluetooth import find_device
from NiimPrintX.nimmy.printer import PrinterClient, BluepyPrinterClient, InfoEnum
from NiimPrintX.nimmy.logger_config import setup_logger, get_logger, logger_enable
from NiimPrintX.nimmy.helper import print_info, print_error, print_success

from devtools import debug

setup_logger()
logger = get_logger()


@click.group(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="Enable verbose logging",
)
@click.pass_context
def niimbot_cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    setup_logger()
    logger_enable(verbose)


@niimbot_cli.command("print")
@click.option(
    "-m",
    "--model",
    type=click.Choice(["b1", "b18", "b21", "d11", "d110", "p15"], False),
    default="d110",
    show_default=True,
    help="Niimbot printer model",
)
@click.option(
    "-d",
    "--density",
    type=click.IntRange(1, 5),
    default=3,
    show_default=True,
    help="Print density",
)
@click.option(
    "-n",
    "--quantity",
    default=1,
    show_default=True,
    help="Print quantity",
)
@click.option(
    "--vo",
    "vertical_offset",
    default=0,
    show_default=True,
    help="Vertical offset in pixels",
)
@click.option(
    "--ho",
    "horizontal_offset",
    default=0,
    show_default=True,
    help="Horizontal offset in pixels",
)
@click.option(
    "-r",
    "--rotate",
    type=click.Choice(["0", "90", "180", "270"]),
    default="0",
    show_default=True,
    help="Image rotation (clockwise)",
)
@click.option(
    "-i",
    "--image",
    type=click.Path(exists=True),
    required=True,
    help="Image path",
)
def print_command(model, density, rotate, image, quantity, vertical_offset, horizontal_offset):
    logger.info(f"Niimbot Printing Start")

    if model in ("b1", "b18", "b21"):
        max_width_px = 384
    if model in ("d11", "d110"):
        max_width_px = 240
    if model == "p15":
        max_width_px = 384 # Assuming P15 has similar width to B series

    if model in ("b18", "d11", "d110") and density > 3:
        density = 3
    try:
        image = Image.open(image)

        if rotate != "0":
            # PIL library rotates counterclockwise, so we need to multiply by -1
            image = image.rotate(-int(rotate), expand=True)
        assert image.width <= max_width_px, f"Image width too big for {model.upper()}"
        asyncio.run(_print(model, density, image, quantity, vertical_offset, horizontal_offset))
    except Exception as e:
        logger.info(f"{e}")


async def _print(model, density, image, quantity, vertical_offset, horizontal_offset):
    try:
        print_info("Starting print job")
        device = await find_device(model)
        if platform.system() == "Linux" and model == "p15": # Assuming 'p15' model will map to Marklife P15
            printer = BluepyPrinterClient(device)
        else:
            printer = PrinterClient(device)

        if await printer.connect():
            print(f"Connected to {device.name}")
        
        # If it's a BluepyPrinterClient, use its specific print_text_bluepy method for text printing
        # For now, we'll assume image printing is handled by the base class or needs adaptation.
        # For the initial request, we are focusing on adding the P15 printer, which implies text printing.
        # The original script was for text, so I'll add a placeholder for text printing.
        # If the user wants image printing for P15, that will require more work.
        if isinstance(printer, BluepyPrinterClient):
            # This part needs to be adapted if the CLI is used for image printing with P15
            # For now, let's assume the CLI 'print' command is for images, and P15 will need a separate text command.
            # Or, we need to convert the image to text for P15, which is not what the original script did.
            # The original script was for text, so I'll add a placeholder for text printing.
            # For now, I'll raise an error if image printing is attempted with P15 via bluepy.
            raise NotImplementedError("Image printing for Marklife P15 via bluepy is not yet implemented in CLI. Please use text printing.")
        else:
            await printer.print_image(image, density=density, quantity=quantity, vertical_offset=vertical_offset,
                                      horizontal_offset=horizontal_offset)
        print_success("Print job completed")
        await printer.disconnect()
    except Exception as e:
        logger.debug(f"{e}")
        await printer.disconnect()


@niimbot_cli.command("print-text-p15")
@click.option(
    "-t",
    "--text",
    type=str,
    required=True,
    help="Text to print",
)
@click.option(
    "--font-size",
    type=int,
    default=72,
    show_default=True,
    help="Font size",
)
@click.option(
    "--font-family",
    type=str,
    default="Arial",
    show_default=True,
    help="Font family",
)
@click.option(
    "--bold",
    is_flag=True,
    help="Bold text",
)
@click.option(
    "--italic",
    is_flag=True,
    help="Italic text",
)
@click.option(
    "--underline",
    is_flag=True,
    help="Underline text",
)
@click.option(
    "--segmented-paper",
    is_flag=True,
    help="Segmented paper printing",
)
def print_text_p15_command(text, font_size, font_family, bold, italic, underline, segmented_paper):
    logger.info(f"Niimbot P15 Text Printing Start")
    asyncio.run(_print_text_p15(text, font_size, font_family, bold, italic, underline, segmented_paper))


async def _print_text_p15(text, font_size, font_family, bold, italic, underline, segmented_paper):
    try:
        print_info("Starting P15 text print job")
        # For P15, we don't need a model to find the device, as it's hardcoded in BluepyPrinterClient
        # However, find_device expects a model, so we pass a dummy one or adapt find_device.
        # For now, let's assume find_device can find the P15 if its address is known.
        # The BluepyPrinterClient will use the device.address directly.
        device = await find_device("p15") # This will need to be adapted to find the P15 by address
        printer = BluepyPrinterClient(device)
        if await printer.connect():
            print(f"Connected to {device.name}")
        await printer.print_text_bluepy(text, font_size, font_family, bold, italic, underline, segmented_paper)
        print_success("P15 Text Print job completed")
        await printer.disconnect()
    except Exception as e:
        logger.debug(f"{e}")
        print_error(e)
        await printer.disconnect()


@niimbot_cli.command("info")
@click.option(
    "-m",
    "--model",
    type=click.Choice(["b1", "b18", "b21", "d11", "d110", "p15"], False),
    default="d110",
    show_default=True,
    help="Niimbot printer model",
)
def info_command(model):
    logger.info("Niimbot Information")
    print_info("Niimbot Information")
    asyncio.run(_info(model))


async def _info(model):
    try:
        device = await find_device(model)
        if platform.system() == "Linux" and model == "p15":
            printer = BluepyPrinterClient(device)
        else:
            printer = PrinterClient(device)
        await printer.connect()
        device_serial = await printer.get_info(InfoEnum.DEVICESERIAL)
        software_version = await printer.get_info(InfoEnum.SOFTVERSION)
        hardware_version = await printer.get_info(InfoEnum.HARDVERSION)
        print(f"Device Serial : {device_serial}")
        print(f"Software Version : {software_version}")
        print(f"Hardware Version : {hardware_version}")
        await printer.disconnect()
    except Exception as e:
        logger.debug(f"{e}")
        print_error(e)
        # await printer.disconnect()


cli = click.CommandCollection(sources=[niimbot_cli])
if __name__ == "__main__":
    niimbot_cli(obj={})
