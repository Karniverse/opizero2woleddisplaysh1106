import os
import psutil
import platform
import socket
import fcntl #delete if didnt work
import struct #delete if didnt work
import netifaces #delete if didnt work
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont
import time
from datetime import datetime

# Display dimensions and layout
width = 128
height = 64

# Line positions for text display
line1 = 2
line2 = 11
line3 = 20
line4 = 31
line5 = 38
line6 = 47
col1 = 4

# Function to do nothing (used in cleanup)
def do_nothing(obj):
    pass

# Function to load the font
def make_font(name, size):
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)


# Initialize the I2C interface and SH1106 display
serial = i2c(port=0, address=0x3C)  # Ensure the I2C port and address are correct
device = sh1106(serial)
device.cleanup = do_nothing

# Use default font for simplicity
#font15 = ImageFont.load_default()
font15 = make_font('FreePixel.ttf', 15)
font14 = make_font('FreePixel.ttf', 14.5)


def bytes2human(n):
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    for i in range(len(symbols)-1, -1, -1):
        unit_size = 1024 ** i
        if n >= unit_size:  # Find the appropriate unit
            value = n / unit_size
            return "%.2f%s" % (value, symbols[i])  # Format with 2 decimals
    return "%.2fB" % n


# Function to get CPU usage
def cpu_usage():
    av1, av2, av3 = os.getloadavg()
    return "%.2f%% %.2f%% %.2f%%" % (av1, av2, av3)

# Function to get CPU temperature
def cpu_temperature():
    tempC = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000
    return "%s°c" % (str(tempC))

# Function to get memory usage
def mem_usage():
    usage = psutil.virtual_memory()
    return "%s / %s" % (bytes2human(usage.used), bytes2human(usage.total))

# Function to get disk usage
def disk_usage(dir):
    usage = psutil.disk_usage(dir)
    return "%s / %s" % (bytes2human(usage.used), bytes2human(usage.total))

# Function to get network stats
def network(iface):
    stat = psutil.net_io_counters(pernic=True)[iface]
    return "NET: %s: Tx%s, Rx%s" % (iface, bytes2human(stat.bytes_sent), bytes2human(stat.bytes_recv))

# Function to get local IP address
def lan_ip():
    f = os.popen("ip route get 1 | awk '/src/ {print $7}'")
    ip = str(f.read())
    return "IP: %s" % ip.rstrip('\r\n').rstrip(' ')

# Function to draw centered text

def draw_centered(y, text, FONT, draw):
    SCREEN_WIDTH = 128
    # Use getbbox() to get the bounding box of the text
    bbox = FONT.getbbox(text)
    width = bbox[2] - bbox[0]  # bbox[2] is the right edge, bbox[0] is the left edge

    # Calculate the horizontal position (centered)
    x = (SCREEN_WIDTH - width) // 2
    
    # Draw the text
    draw.text((x, y), text, font=FONT, fill=255)


# Main function to display system stats
def stats():
    global looper
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 63), outline="white", fill="black")

        if looper == 0:
            draw_centered(line1+5, 'Orangepi Zero 2W', font15, draw)
            draw.text((col1, line4), ' Starting up...', font=font15, fill=255)
            looper = 1
        elif looper == 1:
            draw.text((col1, line1), '----CPU LOAD----', font=font15, fill=255)     
            draw_centered(line2+5, cpu_usage(), font14, draw)
            draw_centered(line4, '----CPU TEMP----', font15, draw)
            draw_centered(line6, cpu_temperature(), font15, draw)
            looper = 2
        elif looper == 2:
            draw_centered(line1, '----MEM Usage---', font15, draw)
            draw_centered(line3-2.5, mem_usage(), font15, draw)
            draw_centered(line4+0.5, '---Disk Usage---', font15, draw)
            draw_centered(line6-1, disk_usage('/'), font15, draw)
            looper = 3
        elif looper == 3:
            draw_centered(line1+6, lan_ip(), font15, draw)
            draw_centered(line4-3.75, "----Hostname----", font15, draw)
            draw_centered(line5+5, "%s" % socket.gethostname(), font15, draw)            
            looper = 4
        else:
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            draw_centered(line1+1, str(datetime.now().strftime('%a %b %d %Y')), font15, draw)
            draw_centered(line3, str(datetime.now().strftime('%I:%M:%S %p')), font14, draw)            
            draw_centered(line4+2.25, '-----Uptime-----', font15, draw)
            draw_centered(line6, "%s" % str(uptime).split('.')[0], font15, draw)
            looper = 1

# Main loop
def main():
    global looper
    looper = 0
    while True:
        stats()
        if looper == 0:
            time.sleep(10)
        else:
            time.sleep(5)

# Run the script
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
