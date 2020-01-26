from liberty.parser import parse_liberty

class ref_list_obj:
    
    def __init__(self):
        print("ref_list_obj init")
        self.ref_list = {}
        
    def add(self,scope,inst):
        module = inst.module_name
        instance = inst.instance_name
        ref = scope+"."+instance
        if module in self.ref_list:
            self.ref_list[module][ref] = inst
        else:
            self.ref_list[module]={ref:inst}

    def __repr__(self):
        return "ref_list({})".format(self.ref_list)

class netlist_tool:
    
    def __init__(self,netlist):
        self.netlist = netlist
        self.ref_list_obj = ref_list_obj()
        
    def extract_refs(self):
        print("extract referenced cells")
        for module in self.netlist.modules:
            current_scope = module.module_name
            for inst in module.module_instances:
                self.ref_list_obj.add(current_scope,inst)
                    
            print(self.ref_list_obj)
            
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