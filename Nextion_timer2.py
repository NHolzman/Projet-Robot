import serial
import time

ser = serial.Serial('/dev/ttyAMA0',9600, timeout=1)

try:
    # Initial setup
    ser.write(b'boutonStop.bco=63519')
    ser.write(b'\xFF\xFF\xFF')
    ser.write(b'ref boutonStop')
    ser.write(b'\xFF\xFF\xFF')

    counter = 0

    while True:
        # Convert seconds → hh:mm:ss
        hours = counter // 3600
        minutes = (counter % 3600) // 60
        seconds = counter % 60

        # Format as 00:00:00
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

        # Send to display (replace timerVar with your actual component)
        cmd = f'timerVar.txt="{time_str}"'
        ser.write(cmd.encode('utf-8'))
        ser.write(b'\xFF\xFF\xFF')

        print(time_str)

        time.sleep(1)
        counter += 1

finally:
    ser.close()