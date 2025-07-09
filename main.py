# Importing necessary modules for hardware communication
from machine import I2C, Pin, UART
# Importing LCD library to interface with a 16x2 LCD display
from gpio_lcd import GpioLcd
# Importing utime for adding delays and working with real-time operations
import utime
# Importing ds1307 library to interface with the RTC (Real-Time Clock) module
import ds1307
#Initializing I2C (Inter-Integrated Circuit) communication for connecting with the RTC module
lcd = GpioLcd(rs_pin=Pin(16),
          enable_pin=Pin(17),
          d4_pin=Pin(18),
          d5_pin=Pin(19),
          d6_pin=Pin(20),
          d7_pin=Pin(21),
          num_lines=2, # LCD has 2 rows
          num_columns=16 # LCD has 16 columns
          )

#Initializing I2C (Inter-Integrated Circuit) communication for connecting with the RTC module 
i2c = I2C(0, scl=Pin(5), sda=Pin(4))  # Using I2C channel 0, SCL connected to GPIO 5, SDA to GPIO 4 
rtc = ds1307.DS1307(i2c, 0x68) # Creating an RTC object with I2C address 0x68 (for DS1307 RTC)

#Initializing UART (Universal Asynchronous Receiver-Transmitter) for communication with an RFID module
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1)) # UART channel 0, transmission on GPIO 0, reception on GPIO 1

# Initializing a button for user Interaction, connected to GPIO 2 with an internal pull-down resistor(reads 1 when pressed)
switch = Pin(2,Pin.IN,Pin.PULL_UP)

#Defining file names to store attendance data
csv_filename1 = "data.csv" # Stores attendance records including name, date, entry time, exit time, and RFID 
csv_filename2 = "details.csv" # Stores user details including name and associated RFID

#Creating or appending to the attendance CSV file and adding headers for data file
with open(csv_filename1, "a") as f:
    f.write("Name,Date,Entry Time,Exit Time,RFID\n")
    f.close()
    
"""
Uncomment the below code to initialize the user details CSV file with sample data
"""
#with open(csv_filename2, "a") as f:
#    f.write("Name,RFID\n")
#    f.write("RABBIT,6F0087C991B0\n")
#    f.write("CAT,6F0087C990B1\n")
#    f.close()
"""
Uncomment and modify the below line to manually set the RTC date & time
Format: (Year, Month, Day, Hour, Minute, Second, Weekday)
"""
rtc.datetime = (2025, 4, 24, 11, 37, 0, 3)


#Main loop runs indefinitely to handle RFID scans and attendance logging
while True:
    # Initializing rfid_data as None before any operations
    rfid_data = None  # Always define before using it in the loop
    # Fetching the current date and time from the RTC module
    date_time = rtc.datetime # Getting a tuple containing date and time details
    date_str = "{:02d}/{:02d}/{:04d}".format(date_time[2], date_time[1], date_time[0]) #Formatting the date
    time_str = "{:02d}:{:02d}:{:02d}".format(date_time[3], date_time[4], date_time[5]) #Formatting the date
    
    # Displaying the current date and time on the LCD screen
    lcd.clear() # Clearing the LCD display before writing new data
    lcd.move_to(0,0) # Moving the cursor to the first row
    lcd.putstr("DATE:" + date_str) # Displaying the formatted date
    lcd.move_to(0,1) # Moving the cursor to the second row
    lcd.putstr("TIME:" + time_str) # Displaying the formatted time
    utime.sleep(1) # Adding a delay to update the display at regular intervals
    
    # Reading button state and RFID input
    x = switch.value() # Checking if the button is pressed
    
    data = uart.read()# Reading data from the RFID module
    
    # If switch is  open, register a new user   
    if x==1:
        lcd.clear()
        lcd.putstr("ENTER NAME.") # Prompt user to enter a name
        print("ENTER YOUR NAME.")
        new_name = input().strip() # Taking user input for name and stripping whitespace
        # If no name is entered, restart the process
        if not new_name:
            print("No input detected. Restarting.")
            lcd.clear()
            utime.sleep(1)
            continue
        lcd.clear()
        lcd.putstr("SCAN CARD.") # Prompt user to scan rfid for register new entry
        print("SCAN THE RFID CARD.")
        utime.sleep(3)  # Give time to scan
        # Reading data from the RFID module
        data = uart.read()
        # If RFID data is received via UART, decode it and remove unnecessary spaces
        if data:
            rfid_data = data.decode("utf-8").strip()
            print("RFID SCANNED:", rfid_data) # Display the scanned RFID in the console
        # If no rfid card is scanned, restart the process
        else:
            print("No RFID scanned.")
            lcd.clear()
            lcd.putstr("NO RFID FOUND")
            utime.sleep(1)
            lcd.clear()
            continue  # Go back to start
     
        # Save the new user's name and RFID into the details CSV file
        with open(csv_filename2, "a") as g:
            g.write("{},{}\n".format(new_name,rfid_data))
            print("Write operation complete")#ensuring successful entry of data
        print("Saved to details.csv: {},{}".format(new_name, rfid_data))
        # Display confirmation message on LCD  
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("SAVED: " + new_name)
        lcd.move_to(0, 1)
        lcd.putstr(rfid_data)
        utime.sleep(3)
        lcd.clear()

        
    # If button is pressed, check and log attendance    
    elif x==0:
        # If RFID data is received via UART, decode it and remove unnecessary spaces
        if data:
            rfid_data = data.decode("utf-8").strip()
            print("RFID SCANNED:", rfid_data) # Display the scanned RFID in the console
     
            lcd.clear()
            name = None # Variable to store matching name if RFID is found
            # Open details.csv to search for a matching RFID entry
            with open(csv_filename2, "r") as g:
                lines = g.readlines()[1:] # Skipping header line
                for line in lines: # Go through each line
                    parts = line.strip().split(",") # Remove extra spaces and split by comma into a list
                    if len(parts) != 2:
                        continue  # If the line doesn't have exactly 2 parts (name and RFID), skip it
                    sname, srfid = parts  #Unpack the name and RFID
                    if srfid == rfid_data:# Check if scanned RFID matches stored RFID
                        print("Data is correct") # Confirm match in console
                        name = sname # Store the name associated with the RFID
                        break  # Stop searching once the name is found

            if name:  # Check if a valid name is found for the scanned RFID
            # Read and update attendance data from the attendance CSV file      
                lines = [] # Initialize an empty list to hold the lines of the CSV
                with open(csv_filename1, "r") as f:
                    lines = f.readlines() # Read all lines from the attendance file

                found = False #Track if an entry is found for updating exit time
                with open(csv_filename1, "w") as f: # Open the file again for writing
                    for line in lines: # Loop through all the lines in the file
                        data = line.strip().split(",")  # Split the line into a list by commas
                        # If entry is found but exit time is missing, update exit time
                        if len(data) >= 5 and data[4] == rfid_data and data[3] == "":
                            data[3] = time_str  # Update the exit time with the current time
                            line = ",".join(data) + "\n" # Reconstruct the line with the updated exit time
                            found = True  # Mark that we found and updated the entry
                        f.write(line) # Write the line (whether updated or not) back to the file
                    # Display a bye message if user is not entering for the first time today
                    if found:
                        lcd.clear()
                        lcd.move_to(0, 0)
                        lcd.putstr("BYE "+sname) # Display the name of the user
                        utime.sleep(1)  # Wait for a second to show the message
                        lcd.clear() # Clear the screen after showing the message
                    
                     # If the user is entering for the first time today, create a new record
                    else :
                        # Add a new record with name, date, time, and RFID
                        f.write("{},{},{},,{}\n".format(name, date_str, time_str, rfid_data)) 
                        # Display a welcome message
                        lcd.clear()
                        lcd.move_to(0, 0)
                        lcd.putstr("WELCOME "+sname) # Display the name of the user
                        utime.sleep(1)  # Wait for a second to show the message
                        lcd.clear() # Clear the screen after showing the message
            # If no valid name was found, meaning the RFID was not recognized, display an error message
            else:
                print("INVALID RFID") # Print to the console for debugging
                lcd.clear() # Clear the LCD screen
                lcd.move_to(0, 0)
                lcd.putstr("INVALID CARD!") # Display 'invalid' on the LCD to notify the user
                utime.sleep(1)  # Wait for a second to show the message
                lcd.clear() # Clear the screen after the message
    
 