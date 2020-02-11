# Verilog Toolkit for Python
Read verilog power&ground netlist and liberty cell library to extract supply pins and generate an equivalent UPF file and verilog netlist without power and ground connections.

## Example
```python
import os.path
from verilog_parser.parser import parse_verilog
from verilog_parser.netlist_tool import netlist_tool

verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/pg_netlist.v')
with open(verilog_file) as f:
    data = f.read()

netlist = parse_verilog(data)
design = netlist_tool(netlist)

design.load_lib("../test_data/ls.lib")
design.extract_refs()

print(design.export_upf("pg_netlist"))
print(design.extract("pg_netlist","netlist"))
```
