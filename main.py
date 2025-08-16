import serial
import serial.tools.list_ports
import time
import sys
import threading
import json
import os
from parser import parse_packet

bms_data = {}
data_lock = threading.Lock()

def update_bms_data(parsed):
    with data_lock:
        if not parsed['checksum_ok']:
            bms_data['error'] = f"   CHECKSUM ERROR - Got: {parsed['checksum_got']:04X}, Expected: {parsed['checksum_calc']:04X}"
            return

        bms_data.pop('error', None)
        bms_data.update(parsed['fields'])

def display_bms_data():
    with data_lock:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{'='*60}")
        print(f"Segway-Ninebot BMS Monitor (Press Ctrl+C to exit)")
        print(f"{'='*60}")

        if 'error' in bms_data:
            print(bms_data['error'])
            print(f"\n{'='*60}")
            return

        # Battery Info
        print("  [BATTERY INFORMATION]")
        print(f"   Serial Number: {bms_data.get('BAT_SN', 'N/A')}")
        print(f"   Firmware Version: {bms_data.get('BAT_FW_VER', 'N/A')}")
        print(f"   Capacity: {bms_data.get('BAT_CAPACITY_mAh', 'N/A')} mAh")
        print(f"   Total Capacity: {bms_data.get('BAT_TOTAL_CAPACITY_mAh', 'N/A')} mAh")
        design_volt = bms_data.get('BAT_DESIGN_VOLT_V')
        print(f"   Design Voltage: {design_volt:.2f} V" if isinstance(design_volt, float) else "   Design Voltage: N/A")
        print(f"   Cycle Count: {bms_data.get('BAT_CYCLE_TIMES', 'N/A')}")
        print(f"   Charge Count: {bms_data.get('BAT_CHARGE_TIMES', 'N/A')}")
        
        # Battery Status
        print("\n  [BATTERY STATUS]")
        print(f"   Remaining Capacity: {bms_data.get('BAT_REMAINING_CAP_mAh', 'N/A')} mAh")
        print(f"   Remaining: {bms_data.get('BAT_REMAINING_CAP_PERCENT', 'N/A')}%") 
        current = bms_data.get('BAT_CURRENT_A')
        if isinstance(current, (int, float)):
            print(f"   Current: {current:.2f} A")
        else:
            print(f"   Current: N/A")
        voltage = bms_data.get('BAT_VOLTAGE_V')
        print(f"   Voltage: {voltage:.2f} V" if isinstance(voltage, float) else "   Voltage: N/A")
        temp1 = bms_data.get('BAT_TEMP1_C')
        temp2 = bms_data.get('BAT_TEMP2_C')
        print(f"   Temperature: {temp1}°C / {temp2}°C" if temp1 is not None and temp2 is not None else "   Temperature: N/A")
        print(f"   Health: {bms_data.get('BAT_HEALTHY_percent', 'N/A')}%") 
        
        # Cell Voltages
        print("\n  [CELL VOLTAGES]")
        cells = bms_data.get('cells', {})
        if cells:
            sorted_cells = sorted(cells.items(), key=lambda item: int(item[0].split('_')[1]))
            for cell_name, cell_voltage in sorted_cells:
                cell_num = cell_name.replace('cell_', '')
                print(f"   Cell {cell_num}: {cell_voltage:.3f} V")
            
            if len(cells) > 1:
                voltages = list(cells.values())
                min_v = min(voltages)
                max_v = max(voltages)
                diff = max_v - min_v
                print(f"   Min: {min_v:.3f}V, Max: {max_v:.3f}V, Diff: {diff:.3f}V")
        else:
            print("   No cell data available.")

        print(f"\n{'='*60}")
        print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

REQUEST_COMMANDS = {
    "info":    bytes.fromhex("5A A5 01 3D 22 01 10 20 6E FF"),
    "status":  bytes.fromhex("5A A5 01 3D 22 01 30 20 4E FF"),
    "cells":   bytes.fromhex("5A A5 01 3D 22 01 40 20 3E FF"),
}

def serial_reader(ser, stop_event):
    buffer = bytearray()
    
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                buffer.extend(ser.read(ser.in_waiting))
                
                while len(buffer) >= 9:
                    start_idx = buffer.find(b'\x5a\xa5')
                    if start_idx == -1:
                        buffer = bytearray()
                        break
                    
                    if start_idx > 0:
                        buffer = buffer[start_idx:]
                    
                    if len(buffer) < 3: break
                    
                    packet_length = buffer[2]
                    total_packet_size = 7 + packet_length + 2
                    
                    if len(buffer) < total_packet_size: break
                    
                    packet_data = bytes(buffer[:total_packet_size])
                    buffer = buffer[total_packet_size:]
                    
                    try:
                        parsed = parse_packet(packet_data)
                        update_bms_data(parsed)
                    except Exception as e:
                        with data_lock:
                            bms_data['error'] = f"Packet parsing error: {e}"
            
        except Exception:
            if not stop_event.is_set():
                print("Serial read error. Stopping.")
                stop_event.set()
        
        time.sleep(0.01)

def serial_writer(ser, stop_event):
    while not stop_event.is_set():
        for name, cmd in REQUEST_COMMANDS.items():
            if stop_event.is_set(): break
            ser.write(cmd)
            time.sleep(0.1)
        
        if stop_event.is_set(): break
        
        time.sleep(0.5)
        
        if not stop_event.is_set():
            display_bms_data()

        for _ in range(20):
            if stop_event.is_set(): break
            time.sleep(0.1)

def select_port():
    ports = serial.tools.list_ports.comports()
    print("Available serial ports:")
    if not ports:
        print("No serial ports found!")
        return None
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")
    while True:
        try:
            choice = int(input("Enter port number to use: "))
            if 0 <= choice < len(ports):
                return ports[choice].device
        except (ValueError, IndexError):
            print("Invalid input. Please enter a number from the list.")

if __name__ == "__main__":
    port_name = select_port()
    if port_name is None:
        sys.exit(1)
    
    ser = None
    stop_event = threading.Event()
    reader_thread = None
    writer_thread = None

    try:
        ser = serial.Serial(port_name, 115200, timeout=0.1)
        print(f"\nSuccessfully opened port {port_name}. Starting monitor...")
        time.sleep(1)
        
        reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event))
        writer_thread = threading.Thread(target=serial_writer, args=(ser, stop_event))
        
        reader_thread.start()
        writer_thread.start()
        
        while not stop_event.is_set():
            if not writer_thread.is_alive() or not reader_thread.is_alive():
                print("\nA thread has unexpectedly stopped. Exiting.")
                stop_event.set()
            time.sleep(0.2)

    except serial.SerialException as e:
        print(f"Error opening or using serial port: {e}")
    except KeyboardInterrupt:
        print("\n\nCtrl+C detected. Stopping monitor...")
    finally:
        if not stop_event.is_set():
            stop_event.set()
        
        print("Waiting for threads to finish...")
        if writer_thread and writer_thread.is_alive():
            writer_thread.join()
        if reader_thread and reader_thread.is_alive():
            reader_thread.join()
        
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        
        print("Program terminated.")
