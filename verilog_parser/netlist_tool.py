from liberty.parser import parse_liberty

class result_string_obj:
    def __init__(self,header):
        self.result = header

    def append(self,string):
        self.result += string

    def __repr__(self):
        return self.result

class mod_obj:
    
    def __init__(self,module):
        self.id = module.module_name
        self.module = module

        self.ref_list = ref_list_obj(self)
        for inst in module.module_instances:
            self.ref_list.add(inst)
            
        self.pg_nets = {}
        
    def add_pg_net(self,pg_net):
        self.pg_nets[pg_net]="primary"
        
    def get_ref(self,inst):
        return(self.ref_list.get(inst.module_name))
    
    def get_related_supply_set(self,net):
        for inst in self.module.module_instances:
            for port in inst.ports:
                if inst.ports[port] == net:
                    ref = self.get_ref(inst).pins[port]
                    if "related_power_pin" in ref:
                        related_power_net = inst.ports[ref["related_power_pin"]]
                        if "related_ground_pin" in ref:
                            related_ground_net = inst.ports[ref["related_ground_pin"]]
                            return("SS_"+related_power_net+"_"+related_ground_net)
        print("Error: could not extract supply set of net {}!".format(net))
        raise
        
    def export_upf(self):
        result = result_string_obj("# export UPF\n\n")

        result.append("\n##############")
        result.append("\n# supply ports")
        result.append("\n##############\n\n")
        for pg_net in self.pg_nets:
            result.append("create_supply_port {}\n".format(pg_net))
            result.append("create_supply_net  {}\n".format(pg_net))
            result.append("connect_supply_net {} -ports {}\n\n".format(pg_net,pg_net))
            

        result.append("\n###################")
        result.append("\n# supply set of IOs")
        result.append("\n###################\n\n")
        module = self.module
        for module_output in module.output_declarations:
            result.append("set_port_attributes -receiver_supply {} -ports {{{}}}\n".format(
                          self.get_related_supply_set(module_output.net_name),
                          module_output.net_name))

        for module_input in module.input_declarations:
            if not (module_input.net_name in self.pg_nets):
                result.append("set_port_attributes -driver_supply {} -ports {{{}}}\n".format(
                              self.get_related_supply_set(module_input.net_name),
                              module_input.net_name))

        result.append("\n################################")
        result.append("\n# power connections of instances")
        result.append("\n################################\n\n")
        for cell_ref in self.ref_list:
            print(" cell_ref:",cell_ref)
            for inst in cell_ref.inst_list:
                for pg_pin in cell_ref.pg_pins:
                    result.append("connect_supply_net {} -ports {}/{}\n".format(cell_ref.inst_list[inst].ports[pg_pin],inst,pg_pin))
                result.append("\n")
            
        return(result)

class ref_obj:
    
    def __init__(self,parent,inst):
        self.inst_list = {}
        self.add(inst)
        self.lib_ref = None
        self.parent = parent
        self.pg_pins = {}
        self.pins = {}
 
    def add(self,inst):
        self.inst_list[inst.instance_name] = inst
        
    def add_lib_ref(self,cell):
        self.lib_ref = cell

        pg_pins = self.lib_ref.get_groups('pg_pin')
        for pg_pin in pg_pins:
            print("    pg_pin:",pg_pin.args[0])
            self.pg_pins[pg_pin.args[0]] = "tbd function"
            
            for inst in self.inst_list:
                print("      connected supply net:",self.inst_list[inst].ports[pg_pin.args[0]])
                self.parent.add_pg_net(self.inst_list[inst].ports[pg_pin.args[0]])
        
        pins = self.lib_ref.get_groups('pin')
        for pin in pins:
            print("    pin:",pin.args[0],pin.attributes)
            self.pins[pin.args[0]] = pin.attributes
        
    def __repr__(self):
        return "pg_pins({}),pins({}),inst_list({})".format(self.pg_pins,self.pins,self.inst_list)

class ref_list_obj:
    
    def __init__(self,parent):
        print("ref_list_obj init")
        self.ref_obj_list = {}
        self.parent = parent
        
    def add(self,inst):
        module = inst.module_name
        if module in self.ref_obj_list:
            self.ref_obj_list[module].add(inst)
        else:
            self.ref_obj_list[module]=ref_obj(self.parent,inst)

    def add_lib_ref(self,cell_name,cell):
        if cell_name in self.ref_obj_list:
            print("add_lib_ref:",cell_name)
            self.ref_obj_list[cell_name].add_lib_ref(cell)
            
    def get(self,cell_name):
        if cell_name in self.ref_obj_list:
            return(self.ref_obj_list[cell_name])

    def __iter__(self):
        self.iter_keys = list(self.ref_obj_list.keys())
        return(self)

    def __next__(self):
        try:
            return(self.ref_obj_list[self.iter_keys.pop()])
        except IndexError:
            raise StopIteration

    def __repr__(self):
        return "ref_list({})".format(self.ref_obj_list)

class netlist_tool:
    
    def __init__(self,netlist):
        self.netlist = netlist
        self.ref_list = ref_list_obj(None)
        self.lib = None

        self.module_list = {}
        for module in self.netlist.modules:
            self.module_list[module.module_name] = mod_obj(module)
        
    def extract_refs(self):
        print("extract referenced cells")
        for module in self.netlist.modules:
            for inst in module.module_instances:
                self.ref_list.add(inst)
                    
            print(self.ref_list)
            
        if self.lib is not None:
            print("liberty file loaded")

            cells = self.lib.get_groups('cell')
            for cell in cells:
                try:
                    cell_name = cell.args[0].value
                except:
                    cell_name = cell.args[0]
                    
#                self.ref_list.add_lib_ref(cell_name, cell)
                for module in self.module_list:
                    self.module_list[module].ref_list.add_lib_ref(cell_name, cell)
            
    def load_lib(self,liberty_file):
        print("load liberty file ",liberty_file)
        try:
            library = parse_liberty(open(liberty_file).read())
        except:
            print("ERROR: could not open liberty file")
            return()
        self.lib = library
        
    def export_upf(self,module):
        if module not in self.module_list:
            raise Exception("module " + module + " does not exist")
        else:
            print("export UPF of module ",module)
            return(self.module_list[module].export_upf())
            
        
    def export(self):
        result = "/* export netlist */\n\n"
        res_obj = result_string_obj("/* export netlist */\n\n")
        
        for module in self.netlist.modules:
            result += "module "
            result += module.module_name
            result += " ("
            
            add_seperator = False
            for port in module.port_list:
                if add_seperator:
                    result += ","
                result += port
                add_seperator = True
            
            result += ");"
            result += "\n\n"
            
            for net in module.net_declarations:
                result += "    wire "
                if net.range is not None:
                    result += "["+str(net.range.start)+":"+str(net.range.end)+"] "
                result += net.net_name
                result += ";\n"
            result += "\n"
            
            for module_instance in module.module_instances:
                result += "    "
                result += module_instance.module_name
                result += " "
                result += module_instance.instance_name
                result += " (\n"
                
                add_seperator = False
                for port in module_instance.ports:
                    if add_seperator:
                        result += ",\n"
                    result += "        ."
                    result += port
                    result += "("
                    result += str(module_instance.ports[port])
                    result += ")"
                    add_seperator = True
                    
                result += "\n"
                result += "    );\n\n"
            
            result += "endmodule"
            result += "\n\n"
           
        
        return(result)