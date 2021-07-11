import LCD_1in44
import LCD_Config
import RPi.GPIO as GPIO
import qrcode
import serial
import sqlite3
import time
import os
import math
from vincenty import vincenty
from PIL import Image,ImageDraw,ImageFont,ImageColor

version = "0.94"
dir = os.path.dirname(__file__)

if dir == "/":
    dir = ""


def init():

    global LCD
    print ("* init() *")

    Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT
    LCD = LCD_1in44.LCD()
    LCD.LCD_Init(Lcd_ScanDir)

    global font
    font = ImageFont.truetype(dir+'pixel.ttf', 10)
    global bigfont
    bigfont = ImageFont.truetype(dir+'pixel.ttf', 20)

    status('LOADING...','blue')

    global menupos
    menupos = 1
    global menuactive
    menuactive = False

    global showrow
    showrow = 0


    print (" -> GPIO")
    status('LOADING... GPIO','blue')
    pins = [6,19,5,26,13,21,20,16] #UP,DOWN,LEFT,RIGHT,PRESS,1,2,3
    GPIO.setmode(GPIO.BCM)

    for i in pins:
        GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(i, GPIO.RISING, callback=btn, bouncetime=200)


    print (" -> GPS")
    status('LOADING... GPS','blue')

    global gps
    global gps_available
    global gps_active
    gps_available = False
    gps_active = False

    try:
        gps = serial.Serial("/dev/ttyACM0", baudrate = 9600, timeout = 0.5)
        gps.close()
        gps_available = True

    except:
        status('LOADING... NO GPS.','red')
        return


    print (" -> SQLITE")
    status('LOADING... SQLITE','blue')

    try:
        f = open(dir+"wunzee.sqlite")
        f.close()

    except IOError:
        update()
        return

    status('LOADING... READY.','blue')

    gps_start()


def btn(channel):
    print ("* btn(%s) *"%channel)

    if channel == 6: #up
        if menuactive:
            menu('up')
    if channel == 21: #key1
        if menuactive:
            menu('up')

    if channel == 13: #press
        gps_stop()
        menu('press')
    if channel == 20: #key2
        gps_stop()
        menu('press')

    if channel == 19: #down
        if menuactive:
            menu('down')
    if channel == 16: #key3
        if menuactive:
            menu('down')

    if channel == 16: #key3
        if menuactive:
            menu('down')

    if channel == 5: #left
        switch()

    if channel == 26: #right
        switch()

def menu(dir):

    global menupos
    global menuactive


    if dir == 'down':
        if menupos != 6:
            menupos += 1
        else:
            menupos = 1

    if dir == 'up':
        if menupos != 1:
            menupos -= 1
        else:
            menupos = 6

    if dir == 'press':
        if menuactive:
            menuactive = False
            print ("run: %i"%menupos)

            if menupos == 1:
                if gps_available:
                    gps_start()
                else:
                    status('LOADING... NO GPS.','red')

            if menupos == 2:
                status('GPS STATUS: TODO...','blue')

            if menupos == 3:
                wlan_status()

            if menupos == 4:
                update('db')

            if menupos == 5:
                update('sys')

            if menupos == 6:
                restart()


            return



    image = Image.new('RGB', (128, 128),"white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 3), 'WUNZEE', font = bigfont, fill = 'blue')

    draw.text((20, 30), 'RUN WUNZEE', font = font, fill = 'black')
    draw.text((20, 45), 'STATUS GPS', font = font, fill = 'black')
    draw.text((20, 60), 'STATUS WLAN', font = font, fill = 'black')
    draw.text((20, 75), 'UPDATE DB', font = font, fill = 'black')
    draw.text((20, 90), 'UPDATE SYSTEM', font = font, fill = 'black')
    draw.text((20, 105), 'RESTART', font = font, fill = 'black')

    draw.text((0, 100), "                \nv%s"%version, font = font, fill = 'blue', align = 'right')

    pos = (menupos * 15) + 15
    draw.text((3, pos), '->', font = font, fill = 'red')

    LCD.LCD_ShowImage(image,0,0)
    print ("set active to true")
    menuactive = True


def restart():
    status("RESTARTING...","red")
    quit()

def gps_parse(data):
    sdata = data.split(",")
    if sdata[2] == 'V':
        #print ("no satellite data available")
        return

    lat = gps_decode(sdata[3])
    lon = gps_decode(sdata[5])

    return [lat,lon]

def gps_decode(coord):
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]

    return round(int(deg) + (float(min+"."+tail)/60),6)

def showstart():

    print ("* showstart() *")

    status('','white')

def update(utype):
    print ("* update(%s) *"%utype)

    status("%sUPDATE..."%utype,"blue")

    import requests
    import subprocess

    try:
        wlan = str(subprocess.check_output(["/sbin/iwgetid -r"], shell = True).strip())

        if utype == "sys":
            os.system("git pull")
            status("%sUPDATE... DONE."%utype, "blue")
            time.sleep(0.5)
            restart()
        else:

            url = 'https://wunzee.gn.uber.space/up.php?'+wlan
            r = requests.get(url,timeout=5)
            if r.content == "fail":
                status("%sUPDATE... FAIL-A"%utype, "blue")
                return

            with open(dir+'wunzee.sqlite','wb') as output_file:
                output_file.write(r.content)

            status("%sUPDATE... DONE."%utype, "blue")


    except subprocess.CalledProcessError as e:
        status('%sUPDATE FAIL-W'%utype, "red")

    except requests.ConnectionError:
        status('%sUPDATE FAIL-S'%utype, "red")


def wlan_status():
        import subprocess

        try:
            wlan = str(subprocess.check_output(["/sbin/iwgetid -r"], shell = True).strip())
            status("WLAN: %s"%wlan, "blue")

        except subprocess.CalledProcessError as e:
            status('WLAN: NO CONN', "red")


def showqr(code,name,showrow,anz,dist):
    print ("* showqr(%s) *"%code)

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(code)

    img = qr.make_image(fill_color="black", back_color="#FFFFFF") # hack as white does not show up anything
    image = img.resize((128, 128))

    draw = ImageDraw.Draw(image)
    if anz > 1:
        draw.text((5, 2), "%i/%i Munzees"%(showrow,anz), font = font, fill = "black")
    draw.text((5, -12), "               \n%im"%dist, font = font, fill = "black",align="right")
    draw.text((5, 114), name, font = font, fill = "black")
    LCD.LCD_ShowImage(image,0,0)

def switch():
    global result_anz
    global showrow
    if showrow < result_anz:
        showrow += 1

def get_db(lat,lon):

    global result_anz
    global showrow

    max_dist = 81 # caution: its a square
    diff_lat = 1.0 / 111111.0 * max_dist
    diff_lon = 1.0 / abs(111111.0*math.cos(lat)) * max_dist

    lat_min = lat - diff_lat
    lat_max = lat + diff_lat
    lon_min = lon - diff_lon
    lon_max = lon + diff_lon


    cos = math.cos(lat*math.pi/180) ** 2

    conn = sqlite3.connect(dir+'wunzee.sqlite')
    cursor = conn.execute("SELECT id,name,qr,lat,lon FROM wunzee WHERE lat > ? AND lat < ? AND lon > ? AND lon < ? ORDER BY ((?-lat)*(?-lat)) + ((? - lon)*(? - lon)*?) ASC",(lat_min,lat_max,lon_min,lon_max,lat,lat,lon,lon,cos))
    result = cursor.fetchall()

    result_anz = len(result)

    if result_anz == 0:
        status("NO MUNZEE NEARBY","blue")
    else:
        if showrow + 1  > result_anz:
            showrow = 0
        dist = vincenty((lat,lon),(result[showrow][3],result[showrow][4]))*1000
        showqr(result[showrow][2],result[showrow][1],showrow+1,result_anz,round(dist))

    conn.close()

def loop():
    print ("* loop() *")
    if gps_available:
        if gps.is_open:
            status("WAITING FOR GPS...","blue")

    try:
        while True:
            if gps_available & gps_active:
                if gps.is_open:
                    data = gps.readline()
                    gpsloop(data)
                #else:
                    #status("GPS NOT OPEN.","red")

    #except serial.serialutil.SerialException:
    #    return
    #    status('CRASH: SERIAL','red')

    except KeyboardInterrupt:
        status('CRASH: ABBRUCH','red')


def gpsloop(data):

    if data[0:6] == "$GPRMC":
        koord = gps_parse(data)
        if koord:
            get_db(koord[0],koord[1])
        else:
            return
            #status("NO GPS DATA","red") #todo: anders anzeigen!


def status(msg,color):
    image = Image.open(dir+'wunzee.bmp')
    draw = ImageDraw.Draw(image)
    draw.text((5, 114), msg, font = font, fill = color)
    LCD.LCD_ShowImage(image,0,0)


def gps_start():
    print ("* gps_start() *")

    status('WAITING FOR GPS...','blue')

    global gps
    global gps_active
    gps_active = True
    gps = serial.Serial("/dev/ttyACM0", baudrate = 9600, timeout = 0.5)


def gps_stop():
    global gps
    global gps_active
    if gps_active:
        print ("* gps_stop() *")
        gps_active = False
        status('STOPPING GPS...','blue')
        time.sleep(0.5)
        gps.close()



if __name__ == '__main__':
    init()
    loop()
