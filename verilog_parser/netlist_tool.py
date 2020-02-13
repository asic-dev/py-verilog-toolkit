from liberty.parser import parse_liberty

class result_string_obj:
    def __init__(self,header):
        self.result = header

    def append(self,string):
        self.result += string

    def __repr__(self):
        return self.result

class netlist_obj:

    '''
    Generic netlist object class that can be iterated
    
    It can execute a dedicated methode with "gen()" that was registered with "gen_reg()" or
    call the methode "gen()" for each item in the internal dictionary. 
    ''' 
    
    def __init__(self,identifier):
        self.id = identifier
        self.__gen_dict = {}
        self.__dict = {}

    def gen(self,gen_type):
        if gen_type in self.__gen_dict:
            return(self.__gen_dict[gen_type]())
        else:
            result = ""
            for item in self.__dict:
                result += self.__dict[item].gen(gen_type)
            return(result)
                
    def gen_reg(self,gen_type,function):
        self.__gen_dict[gen_type] = function

    def add(self,netlist_obj):
        self.__dict[netlist_obj.id]=netlist_obj
        
    def remove(self,identifier):
        try:
            self.__dict.pop(identifier)
        except:
            None
        
    def get(self,identifier):
        return(self.__dict[identifier])

    def __iter__(self):
        self.iter_keys = list(self.__dict.keys())
        return(self)
    
    def __next__(self):
        try:
            return(self.__dict[self.iter_keys.pop()])
        except IndexError:
            raise StopIteration

class net_obj(netlist_obj):
    
    def __init__(self,identifier):
        super().__init__(identifier)        
        self.gen_reg("netlist",self.gen_vlog_decl)

    def gen_vlog_decl(self):
        return("    input {};\n".format(self.id))
   
class inst_obj(netlist_obj):
    
    '''
    object class for a cell instance in the netlist
    
    The constructor requires the reference cell and the parsed verilog of the instance.
    '''
    
    def __init__(self,ref_cell,inst):
        super().__init__(inst.instance_name)
        self.ref_cell = ref_cell
        self.inst = inst
        self.pg_connections = {}
        self.signal_connections = {}
        
        self.gen_reg("upf",self.export_upf)
        self.gen_reg("netlist",self.export_netlist)
        
    def resolve_connectivity(self):
        for pg_pin in self.ref_cell.pg_pins:
            self.pg_connections[pg_pin] = self.inst.ports[pg_pin]
        for pin in self.ref_cell.pins:
            self.signal_connections[pin] = self.inst.ports[pin]

    def export_upf(self):
        result_str = ""
        for pg_pin in self.pg_connections:
            result_str += "connect_supply_net {} -ports {}/{}\n".format(self.pg_connections[pg_pin],
                                                                 self.id,
                                                                 pg_pin)
        return(result_str)

    def export_netlist(self):
        result_str = ""
        result_str += "    {} {} (".format(self.ref_cell.id,self.id)
        for pin in self.signal_connections:
            result_str += "\n        .{}({}),".format(pin,self.signal_connections[pin])
        result_str = result_str[:-1]
        result_str += "\n    );\n\n"
        return(result_str)
    
    def __repr__(self):
        return "(instance:{},pg_pins({}),pins({}))".format(self.id,self.pg_connections,self.signal_connections)

class module_obj:
    
    def __init__(self,module):
        self.id = module.module_name
        self.module = module

        self.ref_list = ref_list_obj(self)
        for inst in module.module_instances:
            self.ref_list.add(inst)
            
        self.pg_nets = {}
        
        self.input_nets = netlist_obj("input_nets")
        for input_net in module.input_declarations:
            self.input_nets.add(net_obj(input_net.net_name))
            
    def add_pg_net(self,pg_net):
        self.pg_nets[pg_net]="primary"
        self.input_nets.remove(pg_net)
        
    def get_ref(self,inst):
        return(self.ref_list.get(inst.module_name))
    
    def get_related_supply_set(self,net):
        for inst in self.module.module_instances:
            for port in inst.ports:
                if inst.ports[port] == net:
                    ref_cell = self.get_ref(inst)
                    ref = ref_cell.pins[port]
                    
                    # check that related power pin is defined in the liberty file of the connected cell
                    if "related_power_pin" in ref:
                        related_power_net = inst.ports[ref["related_power_pin"]]
                    else:
                        raise Exception("no related_power_pin defined for pin {} of cell {}".format(port,inst.module_name))

                    # check that related power pin has the primary power pg_type attribute
                    if not (ref_cell.pg_pins[ref["related_power_pin"]] == "primary_power"):
                        raise Exception("related_power_pin {} should have the attribute primary_power".format(ref["related_power_pin"]))

                    # check that related ground pin is defined in the liberty file of the connected cell
                    if "related_ground_pin" in ref:
                        related_ground_net = inst.ports[ref["related_ground_pin"]]
                    else:
                        raise Exception("no related_ground_pin defined for pin {} of cell {}".format(port,inst.module_name))

                    # check that related ground pin has the primary ground pg_type attribute
                    if not (ref_cell.pg_pins[ref["related_ground_pin"]] == "primary_ground"):
                        raise Exception("related_ground_pin {} should have the attribute primary_ground and not {}".format(
                                        ref["related_ground_pin"],
                                        ref_cell.pg_pins[ref["related_ground_pin"]]))

                    result = {"SS_"+related_power_net+"_"+related_ground_net : {"power":related_power_net,"ground":related_ground_net}}
                    return(result)
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

        ss_dict = {}
        for module_output in module.output_declarations:
            ss_dict.update(self.get_related_supply_set(module_output.net_name))
        for input_net in self.input_nets:
            ss_dict.update(self.get_related_supply_set(input_net.id))
            
        for supply_set in ss_dict:
            result.append("create_supply_set {} -function {{power {}}} -function {{ground {}}}\n".format(
                          supply_set,
                          ss_dict[supply_set]["power"],
                          ss_dict[supply_set]["ground"]))

        result.append("\n")
        
        for module_output in module.output_declarations:
            for supply_set in self.get_related_supply_set(module_output.net_name):
                result.append("set_port_attributes -receiver_supply {} -ports {{{}}}\n".format(
                              supply_set,
                              module_output.net_name))

        result.append("\n")

        for input in self.input_nets:
            for supply_set in self.get_related_supply_set(input.id):
                result.append("set_port_attributes -driver_supply {} -ports {{{}}}\n".format(
                              supply_set,
                              input.id))

        result.append("\n################################")
        result.append("\n# power connections of instances")
        result.append("\n################################\n\n")
        result.append(self.ref_list.gen("upf"))
            
        return(result)
    
    def port_list(self):
        result = ""
        for port in self.module.port_list:
            if not port in self.pg_nets: 
                result += port+","
        result = result[:-1]
        return(result)
    
    def export_netlist(self):
        result = result_string_obj("# export netlist\n\n")
        result.append("module {} ({})\n\n".format(self.id,self.port_list()))
        result.append(self.input_nets.gen("netlist"))
        result.append("\n")
        result.append(self.ref_list.gen("netlist"))
        result.append("endmodule")
        return(result)
    
    def extract(self,extract_type):
        extract_dict={
                "upf":     self.export_upf,
                "netlist": self.export_netlist
            }
        
        return(extract_dict[extract_type]())

class ref_obj(netlist_obj):

    '''
    reference cell: stores a list of all instantiations of the cell.
    '''
    
    def __init__(self,parent,inst):
        super().__init__(inst.module_name)
        self.lib_ref = None
        self.parent = parent
        self.pg_pins = {}
        self.pins = {}
        self.add(inst)
   
    def add(self,inst):
        super().add(inst_obj(self,inst))
        
    def add_lib_ref(self,cell):
        self.lib_ref = cell

        pg_pins = self.lib_ref.get_groups('pg_pin')
        for pg_pin in pg_pins:
            self.pg_pins[pg_pin.args[0]] = pg_pin.attributes["pg_type"]
            
            for instance in self:
                self.parent.add_pg_net(instance.inst.ports[pg_pin.args[0]])
                
        pins = self.lib_ref.get_groups('pin')
        for pin in pins:
            print("    pin:",pin.args[0],pin.attributes)
            self.pins[pin.args[0]] = pin.attributes
            
        # after the pg_pins are extracted for the cell all port connections can be separated into
        # supply and signal connections
        for instance in self:
            instance.resolve_connectivity()

    def __repr__(self):
        return "pg_pins({}),pins({}),inst_list({})".format(self.pg_pins,self.pins,self._netlist_obj__dict)

class ref_list_obj(netlist_obj):
    
    def __init__(self,parent):
        super().__init__("reference_list")
        self.parent = parent
        
    def add(self,inst):
        try:
            self.get(inst.module_name).add(inst)
        except:
            super().add(ref_obj(self.parent,inst))

    def add_lib_ref(self,cell_name,cell):
        try:
            self.get(cell_name).add_lib_ref(cell)
            print("add_lib_ref:",cell_name)
        except:
            None

    def __repr__(self):
        return "ref_list({})".format(self._netlist_obj__dict)

class netlist_tool:
    
    def __init__(self,netlist):
        self.netlist = netlist
        self.ref_list = ref_list_obj(None)
        self.lib = None

        self.module_list = {}
        for module in self.netlist.modules:
            self.module_list[module.module_name] = module_obj(module)
        
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
            
    def extract(self,module,extract_type):
        if module not in self.module_list:
            raise Exception("module " + module + " does not exist")
        else:
            print("export UPF of module ",module)
            return(self.module_list[module].extract(extract_type))
        
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