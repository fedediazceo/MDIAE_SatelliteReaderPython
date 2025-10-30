# XML-driven Satellite Frame Reader

A small dependency-free Python tool to parse fixed-size frames in a binary file according to an XML schema.
(Unless you want to plot something, then you need Matplotlib to use the external plot tool) 

## Highlights
- Validates that the input size is a multiple of the configured frame size.
- Per-file default endianness with optional per-field override.
- Supports types: `u8,i8,u16,i16,u32,i32,u64,i64,f32,float32,f64,float64,bytes` (for `bytes` you must set `bytes="N"` -NOTE: this last thing is untested for now.)
- Calibrations via **safe math expressions** (`expr`) using the raw data variable as `raw` (Example, to multiply the value by 0.3: `raw * 0.3`), or via **plugin functions** (`func`) loaded from a Python file you control.
- Outputs CSV
- Allows to sort by a given specific subsystem field (must use `read_in_memory = true` for this feature)

Example: **schema.xml**:

```xml
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
  </subsystems>
</schema>
```

Settings are in `schema_settings` and the main options for the entire file, namely: 
`read_in_memory` :  if the whole file should be read in memory (for example to process it or sort it) 
                    or if the frames should be read one by one
`sort_by` :  only if `read_in_memory = true`, then you can sort by a field name (NOTE: the field must be present or the sort will fail)
`frame_size` :  fixed frame size. File size should be a multiple of this number, or it will fail
`endian` :  define endianness, either `"little"` or `"big"`
`include_frame_index` :  should the frame number be included in the CSV export

An `offset` in subsystem indicates where the entire subsystem data begins, and then `offset` in each field represents where the frame is located from the start of its subsystem

## Usages

```bash
python sat_reader.py --schema schema.xml --input data.bin --output out.csv
```

```bash
python sat_reader.py --schema schema.xml --input data.bin --output out.csv --plugin date_calibration.py
```

```bash
python sat_reader.py --schema schema.xml --input data.bin --output out.csv --plugin date_calibration.py --csv-delimiter ";"
```

## Calibration safety
- `expr` is a **tiny math domain specific language** that supports: arithmetic, comparisons, ternary `a if cond else b`, and the math library functions (`sin,cos,tan,asin, acos, atan, sqrt, log, log10, exp, fabs, floor, ceil, round, min, max, pow, abs`) (this feature requires more testing)
- Field variable is represented by the `raw` variable. Example: `sin(raw) * 2` 
- For extra logic, code the calibration function in a plugin file and reference it with `func="name"`. Supply the plugin file via command line, and put all the functions there. Then reference each function in the `func` attribute for each field. 

## Notes
- Offsets are 0-based and relative to the **start of each frame**.
- The tool will error if any field overflows the frame boundary.
- CSV columns are: `frame_index` if enabled, plus each `<field name=...>` in schema order.

---
