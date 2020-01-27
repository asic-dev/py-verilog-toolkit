# test_capitalize.py
import os.path
from verilog_parser.parser import parse_verilog
from verilog_parser.netlist_tool import netlist_tool

def test_netlist_export():
    verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/simple_nl_ys.v')
    with open(verilog_file) as f:
        data = f.read()

    netlist = parse_verilog(data)
    
    design = netlist_tool(netlist)
    verilog_export = design.export()
    netlist_reimport = parse_verilog(verilog_export)
    
    assert( str(netlist) == str(netlist_reimport) )
