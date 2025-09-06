#!/usr/bin/env python3

import csv
import sys
import os
from datetime import datetime

# No default CSV path - user must specify

# Import MoTeC format classes from local file
try:
    from motec_ld import MotecLog, MotecChannel, MotecEvent
except ImportError as e:
    print(f"Error importing MoTeC format library: {e}")
    print(f"Make sure motec_ld.py is in the same folder")
    sys.exit(1)

# ALL channels from CSV (excluding first unnamed index column)
ALL_CHANNELS = [
    # (csv_column, csv_header_name, display_name, short_name, units)
    (1, "TS", "Time", "Time", "s"),
    (2, "F_BRAKEPRESSURE", "Front Brake Pressure", "F_BrkPrs", "kPa"),
    (3, "R_BRAKEPRESSURE", "Rear Brake Pressure", "R_BrkPrs", "kPa"),
    (4, "STEERING", "Steering", "Steering", "deg"),
    (5, "FLSHOCK", "FL Shock", "FL_Shock", "mm"),
    (6, "FRSHOCK", "FR Shock", "FR_Shock", "mm"),
    (7, "RRSHOCK", "RR Shock", "RR_Shock", "mm"),
    (8, "RLSHOCK", "RL Shock", "RL_Shock", "mm"),
    (9, "CURRENT", "Current", "Current", "A"),
    (10, "BATTERY", "Battery Voltage", "Battery", "V"),
    (11, "IMU_X_ACCEL", "IMU X Accel", "IMU_X", "g"),
    (12, "IMU_Y_ACCEL", "IMU Y Accel", "IMU_Y", "g"),
    (13, "IMU_Z_ACCEL", "IMU Z Accel", "IMU_Z", "g"),
    (14, "IMU_X_GYRO", "IMU X Gyro", "Gyro_X", "deg/s"),
    (15, "IMU_Y_GYRO", "IMU Y Gyro", "Gyro_Y", "deg/s"),
    (16, "IMU_Z_GYRO", "IMU Z Gyro", "Gyro_Z", "deg/s"),
    (17, "FR_SG", "FR Strain Gauge", "FR_SG", "raw"),
    (18, "FL_SG", "FL Strain Gauge", "FL_SG", "raw"),
    (19, "RL_SG", "RL Strain Gauge", "RL_SG", "raw"),
    (20, "RR_SG", "RR Strain Gauge", "RR_SG", "raw"),
    (21, "FLW_AMB", "FL Wheel Ambient", "FLW_Amb", "C"),
    (22, "FLW_OBJ", "FL Wheel Object", "FLW_Obj", "raw"),
    (23, "FLW_RPM", "FL Wheel RPM", "FLW_RPM", "rpm"),
    (24, "FRW_AMB", "FR Wheel Ambient", "FRW_Amb", "C"),
    (25, "FRW_OBJ", "FR Wheel Object", "FRW_Obj", "raw"),
    (26, "FRW_RPM", "FR Wheel RPM", "FRW_RPM", "rpm"),
    (27, "RRW_AMB", "RR Wheel Ambient", "RRW_Amb", "C"),
    (28, "RRW_OBJ", "RR Wheel Object", "RRW_Obj", "raw"),
    (29, "RRW_RPM", "RR Wheel RPM", "RRW_RPM", "rpm"),
    (30, "RLW_AMB", "RL Wheel Ambient", "RLW_Amb", "C"),
    (31, "RLW_OBJ", "RL Wheel Object", "RLW_Obj", "raw"),
    (32, "RLW_RPM", "RL Wheel RPM", "RLW_RPM", "rpm"),
    (33, "BRAKE_FLUID", "Brake Fluid", "BrkFluid", "raw"),
    (34, "THROTTLE_LOAD", "Throttle Load", "Throttle", "%"),
    (35, "BRAKE_LOAD", "Brake Load", "Brake", "%"),
    (36, "DRS", "DRS", "DRS", "bool"),
    (37, "GPS_LON", "GPS Longitude", "GPS_Lon", "deg"),
    (38, "GPS_LAT", "GPS Latitude", "GPS_Lat", "deg"),
    (39, "GPS_SPD", "GPS Speed", "GPS_Spd", "kph"),
    (40, "GPS_FIX", "GPS Fix", "GPS_Fix", "bool"),
    (41, "ECT", "Engine Coolant Temp", "ECT", "C"),
    (42, "OIL_PSR", "Oil Pressure", "Oil_Prs", "kPa"),
    (43, "TPS", "TPS", "TPS", "%"),
    (44, "APS", "APS", "APS", "%"),
    (45, "DRIVEN_WSPD", "Driven Wheel Speed", "DrWSpeed", "kph"),
    (46, "TESTNO", "Test Number", "TestNo", "num"),
    (47, "DTC_FLW", "DTC FL Wheel", "DTC_FLW", "code"),
    (48, "DTC_FRW", "DTC FR Wheel", "DTC_FRW", "code"),
    (49, "DTC_RLW", "DTC RL Wheel", "DTC_RLW", "code"),
    (50, "DTC_RRW", "DTC RR Wheel", "DTC_RRW", "code"),
    (51, "DTC_FLSG", "DTC FL Strain", "DTC_FLSG", "code"),
    (52, "DTC_FRSG", "DTC FR Strain", "DTC_FRSG", "code"),
    (53, "DTC_RLSG", "DTC RL Strain", "DTC_RLSG", "code"),
    (54, "DTC_RRSG", "DTC RR Strain", "DTC_RRSG", "code"),
    (55, "DTC_IMU", "DTC IMU", "DTC_IMU", "code"),
    (56, "GPS_0_", "GPS 0", "GPS_0", "raw"),
    (57, "GPS_1_", "GPS 1", "GPS_1", "raw"),
    (58, "CH_COUNT", "Channel Count", "CH_Count", "num"),
]


def convert_csv_to_motec_fixed(csv_path, output_filename, max_samples=None):
    """Convert ALL CSV columns to MoTeC with FIXED encoding"""
    
    print("Converting CSV to MoTeC")
    print("=" * 60)
    
    # Read CSV data
    print(f"Reading {csv_path}...")
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        for i, row in enumerate(reader):
            if max_samples and i >= max_samples:
                break
            data.append(row)
    
    print(f"Read {len(data)} samples")
    
    # Calculate frequency
    freq = 500
    if len(data) >= 2:
        try:
            dt = float(data[1][1]) - float(data[0][1])
            if dt > 0:
                freq = int(1.0 / dt)
        except:
            pass
    print(f"Sample rate: {freq} Hz")
    
    # Create MoTeC log
    log = MotecLog()
    now = datetime.now()
    log.date = now.strftime('%d/%m/%Y')
    log.time = now.strftime('%H:%M:%S')
    log.driver = "Driver"
    log.vehicle = "Vehicle"
    log.venue = "Track"
    log.comment = "Fixed - All Channels"
    
    # Create event
    log.event = MotecEvent({
        "name": "Full Data Session",
        "session": "All Channels Fixed",
        "comment": f"All {len(ALL_CHANNELS)} channels with decplaces=0",
        "venuepos": 0
    })
    
    # Add ALL channels
    print(f"\nAdding {len(ALL_CHANNELS)} channels...")
    channels_added = []
    
    for i, (col_idx, csv_name, display_name, short_name, units) in enumerate(ALL_CHANNELS):
        try:
            # Create channel definition with hardcoded defaults (no more channels.py dependency)
            channel_def = {
                "name": display_name,
                "shortname": short_name[:8],  # MoTeC limits to 8 chars
                "units": units,
                "id": 8000 + i,  # Use IDs starting at 8000
                "freq": freq,
                # Fixed defaults that work with MoTeC
                "shift": 0,
                "multiplier": 1,
                "scale": 1,
                "decplaces": 0,
                # Fixed values for compatibility
                "datatype": 0x07,  # float (handles all value ranges)
                "datasize": 4      # 4 bytes for float
            }
            
            channel = MotecChannel(channel_def)
            log.add_channel(channel)
            channels_added.append((col_idx, csv_name))
            
            if i < 10 or i % 10 == 0:  # Show first 10 and every 10th
                print(f"  [{i+1:2}/{len(ALL_CHANNELS)}] {display_name:25} (col {col_idx:2}, {units})")
            
        except Exception as e:
            print(f"  ERROR adding {display_name}: {e}")
    
    print(f"\nSuccessfully added {len(channels_added)} channels")
    
    # Add samples
    print(f"\nConverting samples...")
    sample_count = 0
    
    for row_idx, row in enumerate(data):
        samples = []
        
        for col_idx, csv_name in channels_added:
            try:
                val_str = row[col_idx]
                
                # Handle None and empty values
                if val_str == 'None' or val_str == '':
                    val = 0.0
                else:
                    # NO MODIFICATION - use raw value
                    val = float(val_str)
                
                samples.append(val)
                
            except (IndexError, ValueError):
                samples.append(0.0)
        
        log.add_samples(samples)
        sample_count += 1
        
    
    print(f"\nConversion complete:")
    print(f"  Samples converted: {sample_count}")
    
    # Write output to csv-to-motec/output folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"\nWriting to {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(log.to_string())
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    print(f"\n✓ SUCCESS!")
    print(f"  File: {output_filename}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Channels: {len(channels_added)}")
    print(f"  Samples: {sample_count}")
    
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert CSV to MoTeC format')
    
    # Required CSV input file
    parser.add_argument('csv_file', 
                       help='Path to CSV file to convert')
    
    # Optional arguments
    parser.add_argument('--samples', '-s', type=int, default=None,
                       help='Max samples to convert (default: all)')
    
    args = parser.parse_args()
    
    # Check if CSV exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    # Generate output filename based on input CSV
    csv_basename = os.path.splitext(os.path.basename(args.csv_file))[0]
    output_filename = f"{csv_basename}.ld"
    
    # Convert
    output_path = convert_csv_to_motec_fixed(
        args.csv_file,
        output_filename, 
        args.samples
    )
    
    print("\n" + "=" * 60)
    print("DONE! Load in MoTeC i2:")
    print(f"  File location: {output_path}")


if __name__ == '__main__':
    main()