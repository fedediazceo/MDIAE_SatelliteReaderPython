#!/usr/bin/env python3
"""
Author: Federico Jose Diaz

Small tool to extract frames from a raw satellite dump file using an XML schema.

Responsibilities
- Validates file size is a multiple of defined frame size in schema.
- Reads a defined endianness (little/big) from the schema. 
- Supports integer and float types for field extraction. It's possible to extract bytes, but haven't tested this yet
- Safe calibration expressions (using a small math based domain specific language -check the README.MD for supported functions) 
    and optional plugin defined via a python structure function. In case of transforming raw values to types other than float,
    a plugin function must be used.
- Outputs CSV File with calibrated values defined in the schema and the schema can define:
        - units rounding precision per field
        - include the frame index as first column
        - decide if the file should be read fully in memory or streamed line by line. 

How to use
  python sat_reader.py --schema schema.xml --input data.bin --output out.csv
  python sat_reader.py --schema schema.xml --input data.bin --output out.csv --plugin date_calibration.py
  python sat_reader.py --schema schema.xml --input data.bin --output out.csv --plugin date_calibration.py --csv-delimiter ";"

XML schema example:
<?xml version="1.0" encoding="UTF-8"?>
<schema version="1.0">
    <!-- Frame definition -->
    <schema_settings read_in_memory="true" sort_by="CDH.OBT" frame_size="4000" endian="big" include_frame_index="false"/>
    <!-- Subsystems to extract per frame -->
    <subsystems>
        <subsystem name="PCS" offset="1604">
            <!-- Fields to extract per subsystem -->
            <fields>
                <field name="vBatAverage" type="u16" offset="750">
                    <!-- Calibrate raw units to volts and round to 3 decimals -->
                    <calibration expr="raw * 0.01873128 + (-38.682956)" units="V" round="3"/>
                </field>
            </fields>
        </subsystem>
        <subsystem name="CDH" offset="8">
            <fields>
                <field name="OBT" type="u32" offset="92">
                    <!-- Calibrate date time: convert to a date in a custom function -->
                    <calibration func="obt_seconds_to_datetime"/>
                </field>
            </fields>
        </subsystem>
    </subsystems>
</schema>

"""
import argparse
import os

from sat_reader_dependencies.sat_reader_CSV_export import write_csv_from_file, write_csv_from_data
from sat_reader_dependencies.sat_reader_classes import CalibrationPlugin
from sat_reader_dependencies.sat_reader_parse_xml import parse_schema
from sat_reader_dependencies.sat_reader_read_tools import read_frames
# from extra_tools.search_tool import find_obt_candidates # Uncomment to search for OBT candidates


def main():
    ap = argparse.ArgumentParser(description="Simple generic satellite frame reader using an XML Schema.")
    ap.add_argument("--schema", required=True, help="Path to XML schema file.")
    ap.add_argument("--input", required=True, help="Path to binary frame input file.")
    ap.add_argument("--output", required=True, help="Path to write CSV output file.")
    ap.add_argument("--plugin", help="Optional Python plugin module with calibration functions.", default=None)
    ap.add_argument("--csv-delimiter", help="Optional CSV deliminter character to split columns.", default=None)
    args = ap.parse_args()

    schema = parse_schema(args.schema)

    if not os.path.exists(args.input):
        ap.error(f"[INPUT ERROR] Input not found: {args.input}")

    plugin_module = CalibrationPlugin(args.plugin)

    csv_delimiter = args.csv_delimiter if args.csv_delimiter is not None else ","

    # Validate size multiple without loading the whole file
    file_size = os.path.getsize(args.input)
    if file_size % schema.frame_size != 0:
        ap.error(f"[FILE ERROR] File size {file_size} is not a multiple of frame size {schema.frame_size}.")

    frames_written = 0

    read_in_memory = schema.read_in_memory

    # print(len(find_obt_candidates(args.input))) # Uncomment to search for OBT candidates

    if read_in_memory:
        with open(args.input, "rb") as in_file:
            data = in_file.read()
        
        rows = read_frames(data, schema, plugin_module)

        if schema.sort_by is not None:
            print("sorting by schema field:", schema.sort_by)
            rows = sorted(rows, key=lambda r: r[schema.sort_by])

        frames_written = write_csv_from_data(rows, args.output, csv_delimiter)
    else:
        frames_written = write_csv_from_file(schema, args.input, args.output, plugin_module, csv_delimiter)

    print(f"Wrote {frames_written} rows to {args.output}")

if __name__ == "__main__":
    main()
