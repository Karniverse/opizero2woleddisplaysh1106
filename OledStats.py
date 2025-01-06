import os
import psutil
import platform
import socket
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
font14 = make_font('FreePixel.ttf', 14)

'''
# Function to convert bytes to human-readable format
def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = int(float(n) / prefix[s])
            return '%.2f%s' % (value, s)
    return "%.2f%sB" % n
'''
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
    return "----CPU TEMP----\n     %sc" % (str(tempC))

# Function to get memory usage
def mem_usage():
    usage = psutil.virtual_memory()
    return "\n%s / %s" % (bytes2human(usage.used), bytes2human(usage.total))

# Function to get disk usage
def disk_usage(dir):
    usage = psutil.disk_usage(dir)
    return "\n%s / %s" % (bytes2human(usage.used), bytes2human(usage.total))

# Function to get network stats
def network(iface):
    stat = psutil.net_io_counters(pernic=True)[iface]
    return "NET: %s: Tx%s, Rx%s" % (iface, bytes2human(stat.bytes_sent), bytes2human(stat.bytes_recv))

# Function to get local IP address
def lan_ip():
    f = os.popen("ip route get 1 | awk '{print $NF;exit}'")
    ip = str(f.read())
    return "IP: \n%s" % ip.rstrip('\r\n').rstrip(' ')

# Main function to display system stats
def stats():
    global looper
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 63), outline="white", fill="black")

        if looper == 0:
            draw.text((col1-1, line1+5), 'Orangepi Zero 2W', font=font15, fill=255)
            draw.text((col1, line4), ' Starting up...', font=font15, fill=255)
            looper = 1
        elif looper == 1:
            draw.text((col1, line1), '----CPU LOAD----', font=font15, fill=255)            
            draw.text((col1-1, line2+5), cpu_usage(), font=font14, fill=255)
            draw.text((col1, line4), cpu_temperature(), font=font15, fill=255)
            looper = 2
        elif looper == 2:
            draw.text((col1, line1), '----MEM Usage---', font=font15, fill=255)
            draw.text((col1+4, line1), mem_usage(), font=font15, fill=255)
            draw.text((col1, line4), '---Disk Usage---', font=font15, fill=255)
            draw.text((col1+4, line4), disk_usage('/'), font=font15, fill=255)
            looper = 3
        elif looper == 3:
            draw.text((col1, line1), "%s %s" % (platform.system(), platform.release()), font=font15, fill=255)
            draw.text((col1, line3+5), "----Hostname----\n %s" % socket.gethostname(), font=font15, fill=255)
            #draw.text((col1, line4), lan_ip(), font=font15, fill=255)
            looper = 4
        else:
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            draw.text((col1-2, line1), str(datetime.now().strftime(' %a %b %d %Y\n   %I:%M:%S %p')), font=font15, fill=255)
            draw.text((col1, line4+1), " ----Uptime---- \n %s" % str(uptime).split('.')[0], font=font15, fill=255)
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
