from liberty.parser import parse_liberty

class mod_obj:
    
    def __init__(self,module):
        self.id = module.module_name
        self.module = module

        self.ref_list = ref_list_obj(self)
        for inst in module.module_instances:
            self.ref_list.add(self.id,inst)
            
        self.pg_nets = {}
        
    def add_pg_net(self,pg_net):
        self.pg_nets[pg_net]="primary"
        
    def export_upf(self):
        print ("export UPF for module",self.id)
        print ("  ref_list",self.ref_list)

        module = self.module
        for output in module.output_declarations:
            print("  output:",output)
            wire = output.net_name
            print("    connected wire:",wire)
            
            for inst in module.module_instances:
                for port in inst.ports:
                    if inst.ports[port] == wire:
                        print("      connected instance:",inst," port: ",port)

        for input in module.input_declarations:
            print("  input:",input)

            wire = input.net_name
            print("    connected wire:",wire)
            
            for inst in module.module_instances:
                for port in inst.ports:
                    if inst.ports[port] == wire:
                        print("      connected instance:",inst," port: ",port)
                        
        for pg_net in self.pg_nets:
            print("pg_net:",pg_net)

class ref_obj:
    
    def __init__(self,parent,ref,inst):
        self.inst_list = {}
        self.inst_list[ref] = inst
        self.lib_ref = None
        self.parent = parent
 
    def add(self,ref,inst):
        self.inst_list[ref] = inst
        
    def add_lib_ref(self,cell):
        self.lib_ref = cell

        pg_pins = self.lib_ref.get_groups('pg_pin')
        for pg_pin in pg_pins:
            print("    pg_pin:",pg_pin.args[0])
            
            for inst in self.inst_list:
                print("      connected supply net:",self.inst_list[inst].ports[pg_pin.args[0]])
                self.parent.add_pg_net(self.inst_list[inst].ports[pg_pin.args[0]])
        
        pins = self.lib_ref.get_groups('pin')
        for pin in pins:
            print("    pin:",pin.args[0])
        
    def __repr__(self):
        return "inst_list({})".format(self.inst_list)

class ref_list_obj:
    
    def __init__(self,parent):
        print("ref_list_obj init")
        self.ref_obj_list = {}
        self.parent = parent
        
    def add(self,scope,inst):
        module = inst.module_name
        instance = inst.instance_name
        ref = scope+"."+instance
        if module in self.ref_obj_list:
            self.ref_obj_list[module].add(ref,inst)
        else:
            self.ref_obj_list[module]=ref_obj(self.parent,ref,inst)

    def add_lib_ref(self,cell_name,cell):
        if cell_name in self.ref_obj_list:
            print("add_lib_ref:",cell_name)
            self.ref_obj_list[cell_name].add_lib_ref(cell)

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
            current_scope = module.module_name
            for inst in module.module_instances:
                self.ref_list.add(current_scope,inst)
                    
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
            self.module_list[module].export_upf()
            
        
    def export(self):
        result = "/* export netlist */\n\n"
        
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