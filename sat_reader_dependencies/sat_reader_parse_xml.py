"""
Author: Federico Jose Diaz

XML schema parser for SAT Reader.
Parses an XML file defining the schema into Schema, Subsystems and Field objects.
    
- Validates required attributes and elements.
- Supports optional calibration expressions and plugin function names.

XML schema example:
<?xml version="1.0" encoding="UTF-8"?>
<schema version="1.0">
  <schema_settings read_in_memory="true" sort_by="CDH.OBT" frame_size="4000" endian="big" include_frame_index="false"/>
  <subsystems>
    <subsystem name="PCS" offset="1604">
      <fields>
        <field name="vBatAverage" type="u16" offset="750">
          <calibration expr="raw * 0.01873128 + (-38.682956)" units="V" round="5"/>
        </field>
      </fields>
    </subsystem>
</schema>
"""

from typing import Dict, List
import xml.etree.ElementTree as ET

from sat_reader_dependencies.sat_reader_classes import Field, Schema, Subsystem

def parse_schema(path: str) -> Schema:
    """
    Parse the XML schema file at the given path into a Schema object.
    Raises ValueError for any validation errors.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    
    if root.tag != "schema":
        raise ValueError("[XML_ERROR] Root element must be <schema>")

    schema_settings = root.find("schema_settings")

    if schema_settings is None:
        raise ValueError("[XML_ERROR] <schema_settings> element is required")
    
    TRUTH_STRINGS = {"true", "yes", "1"}
    FALSE_STRINGS = {"false", "no", "0"}

    attribute_read_in_memory = schema_settings.attrib.get("read_in_memory", None)

    if attribute_read_in_memory is None:
        raise ValueError("[XML_ERROR] <schema_settings read_in_memory> must be defined and be true, false, yes, no, 1 or 0")

    attribute_read_in_memory = attribute_read_in_memory.lower()

    if attribute_read_in_memory not in TRUTH_STRINGS and attribute_read_in_memory not in FALSE_STRINGS:
        raise ValueError("[XML_ERROR] <schema_settings read_in_memory> must be defined and be true, false, yes, no, 1 or 0")

    read_in_memory = attribute_read_in_memory in TRUTH_STRINGS

    sort_by = schema_settings.attrib.get("sort_by", None)

    if sort_by is not None and read_in_memory is False:
        raise ValueError("[XML_ERROR] <schema_settings sort_by> can only be used if read_in_memory is true")

    frame_size = int(schema_settings.attrib.get("frame_size", "0"))

    if frame_size <= 0:
        raise ValueError("[XML_ERROR] <schema_settings frame_size> must be positive and not 0")
    
    default_endian = schema_settings.attrib.get("endian", "little").lower()

    if default_endian not in ("little", "big"):
        raise ValueError("[XML_ERROR] <frame endian> must be 'little' or 'big'")
    
    attribute_include_frame_index = schema_settings.attrib.get("include_frame_index", None)

    if attribute_include_frame_index is None:
        raise ValueError("[XML_ERROR] <schema_settings attribute_include_frame_index> must be defined and be true, false, yes, no, 1 or 0")

    attribute_include_frame_index = attribute_include_frame_index.lower()

    if attribute_include_frame_index not in TRUTH_STRINGS and attribute_include_frame_index not in FALSE_STRINGS:
        raise ValueError("[XML_ERROR] <schema_settings attribute_include_frame_index> must be defined and be true, false, yes, no, 1 or 0")

    include_frame_index = attribute_include_frame_index in TRUTH_STRINGS

    subsystem_elem = root.find("subsystems")
    if subsystem_elem is None:
        raise ValueError("[XML_ERROR] <subsystems> element is required")    
    
    subsystems: List[Dict[Subsystem, List[Field]]] = []

    for se in subsystem_elem.findall("subsystem"):
        subsystem_name = se.attrib["name"]
        subsystem_offset = int(se.attrib["offset"])

        fields_elem = se.find("fields")
        if fields_elem is None:
            raise ValueError("[XML_ERROR] <subsystem> -> <fields> element is required")

        fields: List[Field] = []

        for fe in fields_elem.findall("field"):
            name = fe.attrib["name"]
            byte_type = fe.attrib["type"]
            offset = int(fe.attrib["offset"])

            byte_len = fe.attrib.get("bytes")
            byte_len = int(byte_len) if byte_len is not None else None 

            calib_expr = None
            calib_func = None
            units = None
            round_digits = None

            cal = fe.find("calibration")
            if cal is not None:
                calib_expr = cal.attrib.get("expr")
                calib_func = cal.attrib.get("func")
                units = cal.attrib.get("units")
                if cal.attrib.get("round"):
                    round_digits = int(cal.attrib["round"])

                if calib_expr and calib_func:
                    raise ValueError(f"[XML_ERROR] field {name}: use either calibration expr or func, not both")

            fields.append(
                    Field(
                        name=name, 
                        type=byte_type, 
                        offset=offset,
                        bytes=byte_len, 
                        calibration_expression=calib_expr, 
                        calibration_plugin=calib_func,
                        units=units, 
                        round_digits=round_digits
                    )
            )
        
        subsystems.append({Subsystem(name=subsystem_name, offset=subsystem_offset, fields=fields): fields})

    return Schema(
                read_in_memory=read_in_memory,
                frame_size=frame_size, 
                default_endian=default_endian,
                include_frame_index=include_frame_index, 
                subsystems=subsystems,
                sort_by=sort_by
            )
