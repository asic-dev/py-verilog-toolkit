# test_capitalize.py
import os.path
from verilog_parser.parser import parse_verilog

def test_netlist_read():
    verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/simple_nl_ys.v')
    with open(verilog_file) as f:
        data = f.read()

    netlist = parse_verilog(data)
    
    module = netlist.modules.pop()
    assert ('dummy' == module.module_name)

    module = netlist.modules.pop()
    assert ('alu_shift' == module.module_name)
