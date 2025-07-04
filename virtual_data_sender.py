#Link a com input to another to test the software. This is the sender part of the code
#The GUI is the receiver. Send to COM2 and the receiver reads in COM1


import json
import random
import serial
import time

def generate_random_json():
    humidities = [random.randint(0, 99) for _ in range(16)]
    temperatures = [random.randint(25, 61) for _ in range(140)]

    #Have n cells without temp sensors
    loc = [random.randint(0, 139) for _ in range(50)]
    for i in loc:
        temperatures[i] = 0

    voltages = [random.uniform(2.95, 4.35) for _ in range(140)]
    pec_errors = [random.randint(0, 15) for _ in range(16)]
    balancing = [random.randint(0, 1) for _ in range(144)]

    accumulator_info = { 
        "Ams_Error": str(random.choice([0, 1])),
        "Imd_Error": str(random.choice([0, 1])),
        "AIR_P_Supp": str(random.choice([0, 1])),
        "AIR_M_Supp": str(random.choice([0, 1])),
        "AIR_P_State": str(random.choice([0, 1])),
        "AIR_M_State": str(random.choice([0, 1])),
        "over60_dclink": str(random.choice([0, 1])),
        "dc_dc_temp": "{:.4f}".format(random.uniform(0, 100)),
        "HVroom_humidity": str(random.randint(0, 100)),
        "precharge_voltage": "{:.4f}".format(random.uniform(0, 800)),
        "AIR_P_State_Int": str(random.choice([0, 1]))
    }

    isabelle_info = {
        "V_Side_Voltage": "{:.1f}".format(random.uniform(0, 800)),
        "Current": "{:.2f}".format(random.uniform(0, 100)),
        "Ah_consumed": "{:.3f}".format(random.uniform(0, 50)),
        "Energy Consumed": str(random.randint(0, 500))
    }

    elcon_info = {
        "Target_Voltage": "{:.1f}".format(random.uniform(0, 800)),
        "Output_Voltage": "{:.1f}".format(random.uniform(0, 800)),
        "Target_Current": "{:.1f}".format(random.uniform(0, 100)),
        "Output_Current": "{:.1f}".format(random.uniform(0, 100)),
        "Elcon_connected": str(random.choice([0, 1])),
        "Elcon_AC_input_OK": str(random.choice([0, 1])),
        "CANBUS_Error": str(random.choice([0, 1])),
        "Target_charge_state": str(random.choice([0, 1])),
        "Elcon_charge_status": str(random.choice([0, 1])),
        "Elcon_overtemp": str(random.choice([0, 1]))
    }

    w = random.randint(0, 7)
    if w == 0: data = {"AccumulatorInfo": accumulator_info}
    elif w == 1: data = {"Isabelle Info": isabelle_info}
    elif w == 2: data = {"Elcon Info": elcon_info}
    elif w == 3: data = {"Humidities": humidities}
    elif w == 4: data = {"Temperatures": temperatures}
    elif w == 5: data = {"Voltages": voltages}
    elif w == 6: data = {"PEC_Errors": pec_errors}
    else: data = {"Balancing": balancing}

    return data

def chunk_string(s, min_size=50, max_size=200):
    chunks = []
    i = 0
    while i < len(s):
        size = random.randint(min_size, max_size)
        chunks.append(s[i:i+size])
        i += size
    return chunks

def send_json_via_serial(data, port, baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        json_string = json.dumps(data) + '\n'
        chunks = chunk_string(json_string)

        for chunk in chunks:
            ser.write(chunk.encode('utf-8'))
            time.sleep(0.05)  # shorter delay between transmissions

        ser.close()
        return chunks
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    serial_port = "COM2"
    i = 1
    
    while True:
        random_data = generate_random_json()
        chunks = send_json_via_serial(random_data, serial_port) #Unorganized syntax but fine for now
        time.sleep(0.1)
        
        for chunk in chunks:
            print("Sent data pack: " + chunk)
