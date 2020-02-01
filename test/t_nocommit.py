import os.path
from verilog_parser.parser import parse_verilog
from verilog_parser.netlist_tool import netlist_tool

#verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/simple_nl_ys.v')
verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/pg_netlist.v')
with open(verilog_file) as f:
    data = f.read()

netlist = parse_verilog(data)

design = netlist_tool(netlist)
verilog_export = design.export()
print(verilog_export)

netlist_reimport = parse_verilog(verilog_export)

print(netlist.modules)
print(netlist_reimport.modules)
assert(str(netlist) == str(netlist_reimport))

design.load_lib("../test_data/ls.lib")
design.extract_refs()

upf = design.export_upf("pg_netlist")

print(upf)
    