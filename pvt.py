#!/usr/bin/python3
import argparse
import sys
from verilog_parser.parser import parse_verilog
from verilog_parser.netlist_tool import netlist_tool

def main():
    print ("\npy-verilog-toolkit\n\n")

    parser = argparse.ArgumentParser()
    
    parser.add_argument("-ni",
                        "--netlist_in",
                        type = str,
                        help = "power&ground verilog netlist",
                        required = True)
    
    parser.add_argument("-l",
                        "--liberty_file",
                        type = str,
                        help = "liberty file for instantiated cells",
                        required = True)
    
    parser.add_argument("-m",
                        "--module",
                        type = str,
                        help = "top module for extraction",
                        required = True)
    
    args = parser.parse_args()

    try:
        verilog_file = args.netlist_in
        with open(verilog_file) as f:
            data = f.read()
    except:
        sys.exit("ERROR: could not open input netlist")
        
    try:
        netlist = parse_verilog(data)
        design = netlist_tool(netlist)
        print(netlist)
    except:
        sys.exit("ERROR: could not parse verilog power&ground netlist")
        
    try:
        design.load_lib(args.liberty_file)
        design.extract_refs()
        print(design.export_upf("pg_netlist"))
    except:
        sys.exit("ERROR: could not load cell library")
        
    try:
        exported_upf = design.export_upf(args.module)
        print(exported_upf)
    except:
        sys.exit("ERROR: could not export upf data")
        

if __name__ == "__main__":
    main()