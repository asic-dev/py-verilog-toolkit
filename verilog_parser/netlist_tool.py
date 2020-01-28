from liberty.parser import parse_liberty

class ref_obj:
    
    def __init__(self,ref,inst):
        self.inst_list = {}
        self.inst_list[ref] = inst
        self.lib_ref = None

    def add(self,ref,inst):
        self.inst_list[ref] = inst
        
    def add_lib_ref(self,cell):
        self.lib_ref = cell

        pg_pins = self.lib_ref.get_groups('pg_pin')
        for pg_pin in pg_pins:
            print("    pg_pin:",pg_pin.args[0])
        
        pins = self.lib_ref.get_groups('pin')
        for pin in pins:
            print("    pin:",pin.args[0])
        
    def __repr__(self):
        return "inst_list({})".format(self.inst_list)

class ref_list_obj:
    
    def __init__(self):
        print("ref_list_obj init")
        self.ref_obj_list = {}
        
    def add(self,scope,inst):
        module = inst.module_name
        instance = inst.instance_name
        ref = scope+"."+instance
        if module in self.ref_obj_list:
            self.ref_obj_list[module].add(ref,inst)
        else:
            self.ref_obj_list[module]=ref_obj(ref,inst)

    def add_lib_ref(self,cell_name,cell):
        if cell_name in self.ref_obj_list:
            print("add_lib_ref:",cell_name)
            self.ref_obj_list[cell_name].add_lib_ref(cell)

    def __repr__(self):
        return "ref_list({})".format(self.ref_obj_list)

class netlist_tool:
    
    def __init__(self,netlist):
        self.netlist = netlist
        self.ref_list = ref_list_obj()
        self.lib = None
        
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
                    
                self.ref_list.add_lib_ref(cell_name, cell)
            
    def load_lib(self,liberty_file):
        print("load liberty file ",liberty_file)
        try:
            library = parse_liberty(open(liberty_file).read())
        except:
            print("ERROR: could not open liberty file")
            return()
        self.lib = library
        
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