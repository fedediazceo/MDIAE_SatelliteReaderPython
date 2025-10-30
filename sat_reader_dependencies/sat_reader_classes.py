"""
Author: Federico Jose Diaz

Classes representing the schema and plugin system for the SAT reader.

Includes:
- Field: Represents a single data field in the schema.
- Subsystem: Represents a subsystem containing multiple fields.
- Schema: Represents the overall schema including frame size and subsystems.
- Plugin: Loads and manages optional calibration plugins.

Note: 
    Field, Subsystem, and Schema classes Uses Optional for fields that may not be present,
    and the dataclass decorator for automatic code generation.

"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import importlib.util

"""
Field class 

Represents a single data field in the schema.
"""
@dataclass
class Field:
    name: str
    type: str
    offset: int  # relative to frame start
    # Optional fields
    bytes: Optional[int] = None  # number of bytes for this field. Should be bytes * size(type) if applicable 
    # Calibration: can be the expression defined in the schema, or a function name to call from the plugin
    calibration_expression: Optional[str] = None
    calibration_plugin: Optional[str] = None
    units: Optional[str] = None
    # Precision for rounding calibrated float values. None means default float behavior.
    round_digits: Optional[int] = None
"""
Subsystem class 

Represents a subsystem in the schema.
Holds a list of fields and its base offset relative to frame start.

Explanation on this class:
The subsystem class objects will be used as keys in dictionaries within the Schema class.
Because dataclass instances are not hashable by default when they contain mutable fields (like lists),
I have to set unsafe_hash=True to allow them to be used as dictionary keys.
In the mutable `fields` attribute, I set compare=False and hash=False to exclude it from the generated
__hash__ and __eq__ methods, since lists are mutable and not hashable.
BUT, the name and offset attributes will NOT CHANGE in my code, and are sufficient to uniquely identify a Subsystem.
So, as long as those don't change, I'm safe. And I won't change them, since they define the Subsystem.
"""
@dataclass(unsafe_hash=True)
class Subsystem:
    name: str
    offset: int  # relative to frame start
    fields: List[Field] = field(default_factory=list, compare=False, hash=False)
"""
Schema class

Represents the overall schema including frame size, endianness,
whether to check size multiple, the list of subsystems, and if the dataset should be sorted.
"""
@dataclass
class Schema:
    read_in_memory: bool
    frame_size: int
    default_endian: str
    include_frame_index: bool
    subsystems: List[Dict[Subsystem, List[Field]]]
    sort_by: Optional[str] = None # field name to sort by when read_in_memory is True


"""
Plugin class

- Manages loading and calling calibration plugins (if present)
    supplied via command line for a defined value in the schema.

Responsibilities:
- Load the plugin module from a given file path.
- Check if a function exists in the plugin.
- Call a function from the plugin with provided arguments.
"""
class CalibrationPlugin:
    def __init__(self, module_path: Optional[str] = None):
        self.module = None
        if module_path:
            spec = importlib.util.spec_from_file_location("sat_reader_plugin", module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"[PLUGIN ERROR] Cannot load calibration plugin from {module_path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  
            self.module = mod

    def has(self, name: str) -> bool:
        return self.module is not None and hasattr(self.module, name)

    def call(self, name: str, raw: Any) -> Any:
        if not self.module:
            raise RuntimeError("[PLUGIN ERROR] No plugin module loaded.")
        fn = getattr(self.module, name, None)
        if not callable(fn):
            raise AttributeError(f"[PLUGIN ERROR] Plugin has no callable '{name}' calibration function.")
        # executes calibration function from plugin with raw value and frame index
        return fn(raw)