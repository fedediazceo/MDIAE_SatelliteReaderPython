"""
Binary data reading and frame decoding tools.

- Functions to read binary data frames according to a schema.
- Unpack raw bytes into defined types with endianness.
- Apply calibration expressions or plugin functions to raw values.

"""

from typing import Any, Dict, List, Optional
import struct

from sat_reader_dependencies.sat_reader_classes import Schema, CalibrationPlugin
from sat_reader_dependencies.sat_reader_parse_calibration import eval_expr

"""
Mapping of supported types to struct module format codes.
I did this because I always forget them and it's easier to read this way.
""" 
_STRUCT_CODES = {
    "u8": "B", "i8": "b",
    "u16": "H", "i16": "h",
    "u32": "I", "i32": "i",
    "u64": "Q", "i64": "q",
    "f32": "f", "float32": "f",
    "f64": "d", "float64": "d",
}

def type_size(byte_type: str, byte_len: Optional[int]) -> int:
    """
    Get the size in bytes of the given type.
    Raises ValueError for unknown types.
    """
    if byte_type in _STRUCT_CODES:
        return {"B":1,"b":1,"H":2,"h":2,"I":4,"i":4,"Q":8,"q":8,"f":4,"d":8}[_STRUCT_CODES[byte_type]]
    if byte_type == "bytes":
        if not byte_len or byte_len <= 0: # this is untested with the current file provided.
            raise ValueError("[TYPE ERROR] bytes type requires a positive 'bytes' attribute")
        return int(byte_len)
    raise ValueError(f"[TYPE ERROR] Unknown field type '{byte_type}'.")

def unpack_value(data: bytes, byte_type: str, endian: str) -> Any:
    """
    Unpack raw bytes into the specified type with given endianness.
    Supports integer, float types and raw bytes. This last one I coulnd't test
    Raises ValueError for unknown types.
    """
    if byte_type == "bytes":
        return data  # return raw bytes (for now untested)
    code = _STRUCT_CODES[byte_type]
    prefix = "<" if endian == "little" else ">"
    return struct.unpack(prefix + code, data)[0]

def read_frames(data: bytes, schema: Schema, calibration_plugin: CalibrationPlugin) -> List[Dict[str, Any]]:
    """
    Read and decode all frames from binary data according to the schema.
    Applies calibration expressions or plugin functions as defined in the schema.
    Returns a list of dictionaries, each representing a decoded frame.
    This is used when all data is read in memory.
    """

    frame_count = len(data) // schema.frame_size # they are a multiple at this point, so this is exact, using the // returns an int
    
    results: List[Dict[str, Any]] = []

    for frame_index in range(frame_count):
        base = frame_index * schema.frame_size
        frame_data = data[base:base + schema.frame_size]
        row = decode_frame(frame_data, schema, calibration_plugin, frame_index)
        results.append(row)
    return results

def decode_frame(frame: bytes, schema: Schema, plugin: CalibrationPlugin, frame_index: int) -> Dict[str, Any]:
    """
    Decode a single frame of binary data according to the schema.
    Applies calibration expressions or plugin functions as defined in the schema.
    Returns a dictionary representing the decoded frame.
    This is used for both in memory and streaming reading.
    """
    row: Dict[str, Any] = {}
    
    if schema.include_frame_index:
        row = {"frame_index": frame_index}
    endian = schema.default_endian

    for subsystem_dict in schema.subsystems:
        for subsystem, fields in subsystem_dict.items():
            for field in fields:
                size = type_size(field.type, field.bytes)
                start = subsystem.offset + field.offset
                end = start + size
                if end > schema.frame_size:
                    raise ValueError(f"[READ ERROR] Field '{field.name}' (offset {field.offset}, size {size}) overflows frame boundary.")
                
                raw_bytes = frame[start:end]
                raw_val = unpack_value(raw_bytes, field.type, endian)

                calibrated = raw_val

                # expression is provided directly in schema
                if field.calibration_expression:
                    calibrated = eval_expr(field.calibration_expression, raw=float(raw_val))
                # expression is provided via calibration plugin function
                elif field.calibration_plugin:
                    if not plugin.has(field.calibration_plugin):
                        raise ValueError(f"[PLUGIN ERROR] Calibration function '{field.calibration_plugin}' not found in plugin.")
                    calibrated = plugin.call(field.calibration_plugin, raw_val)
                # Rounding
                if isinstance(calibrated, float) and field.round_digits is not None:
                    calibrated = round(calibrated, field.round_digits)

                row[subsystem.name+"."+field.name] = calibrated
    
    return row