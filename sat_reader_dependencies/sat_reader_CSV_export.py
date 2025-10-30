"""
CSV export helper function.

- Reads a list of dictionaries and writes them to a CSV file.
- If the list is empty, creates an empty file.
- Uses the keys of the first dictionary as the CSV header.

"""

import csv
from typing import Any, Dict, List

from sat_reader_dependencies.sat_reader_classes import CalibrationPlugin, Schema
from sat_reader_dependencies.sat_reader_read_tools import decode_frame

def write_csv_from_data(rows: List[Dict[str, Any]], out_path: str, delimiter:str = ",") -> None:
    """
    Write a list of dictionaries to a CSV file.
    If the list is empty, creates an empty file.
    Uses the keys of the first dictionary as the CSV header.
    Returns the number of rows written.
    """
    if not rows:
        with open(out_path, "w", newline="", encoding="utf-8") as csv_file:
            csv_file.write("")
        return
    
    fieldnames = list(rows[0].keys())
    frame_index = 0
    
    with open(out_path, "w", newline="", encoding="utf-8") as csv_file:
        w = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=delimiter)
        w.writeheader()
        for r in rows:
            w.writerow(r)
            frame_index += 1
    
    return frame_index

def write_csv_from_file(schema: Schema, in_path: str, out_path: str, plugin_module: CalibrationPlugin, delimiter = ",") -> int:
    """
    Read frames from a binary file and write them to a CSV file according to the schema.
    Applies calibration expressions or plugin functions as defined in the schema.
    Returns the number of rows written.
    """
    if schema.include_frame_index:
        fieldnames = ["frame_index"] + [f.name for f in schema.fields]
    else:
        fieldnames = [f.name for f in schema.fields]
    
    with open(out_path, "w", newline="", encoding="utf-8") as out_file, open(in_path, "rb") as in_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        frame_index = 0
        while True:
            frame = in_file.read(schema.frame_size)
            if not frame:
                break
            if len(frame) != schema.frame_size:
                raise ValueError("[READ ERROR] Partial frame encountered at end of file.")
            row = decode_frame(frame, schema, plugin_module, frame_index)
            writer.writerow(row)
            frame_index += 1
    
    return frame_index