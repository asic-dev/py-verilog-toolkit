import os.path


def verilog_netlist() -> str:
    """
    Get content of an example Verilog netlist.
    :return:
    """
    verilog_file = os.path.join(os.path.dirname(__file__), '../test_data/simple_nl_ys.v')
    with open(verilog_file) as f:
        data = f.read()
    return data
