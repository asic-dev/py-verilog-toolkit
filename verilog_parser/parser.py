from lark import Lark, Transformer, v_args

from typing import Dict, List

# http://www.verilog.com/VerilogBNF.html

verilog_netlist_grammar = r"""
    ?start: description*
    
    ?description: module
    
    ?module: "module" identifier list_of_ports? ";" module_item* "endmodule"
    
    list_of_ports: "(" port ("," port)* ")"
    ?port: identifier
        | named_port_connection
    
    ?module_item: input_declaration
        | output_declaration
        | net_declaration
        | continuous_assign
        | module_instantiation
    input_declaration: "input" range? list_of_variables ";"
    
    output_declaration: "output" range? list_of_variables ";"
    
    net_declaration: "wire" range? list_of_variables ";"
    
    continuous_assign: "assign" list_of_assignments ";"
    
    list_of_assignments: assignment ("," assignment)*
    
    assignment: lvalue "=" expression
    
    lvalue: identifier
        | identifier_indexed
        | identifier_sliced
        | concatenation
        
    concatenation: "{" expression ("," expression)* "}"
    
    ?expression: identifier
        | identifier_indexed
        | identifier_sliced
        | concatenation
        | number
    
    identifier_indexed: identifier "[" uint "]"
    identifier_sliced: identifier range
    
    module_instantiation: identifier module_instance ("," module_instance)* ";"
    
    module_instance: identifier "(" list_of_module_connections? ")"
    
    list_of_module_connections: module_port_connection ("," module_port_connection)*
        | named_port_connection ("," named_port_connection)*
        
    module_port_connection: expression
    
    named_port_connection: "." identifier "(" expression ")"
    
    identifier: CNAME
    
    ?range: "[" uint ":" uint "]"
    
    ?list_of_variables: identifier ("," identifier)*

    string: ESCAPED_STRING

    // FIXME TODO: Use INT
    uint: SIGNED_NUMBER
    
    number: uint base uint -> number_explicit_length
        | base uint -> number_implicit_length
    
    base: BASE
    BASE: "'b" | "'B" | "'h" | "'H'"

    COMMENT_SLASH: /\/\*(\*(?!\/)|[^*])*\*\//
    COMMENT_BRACE: /\(\*(\*(?!\))|[^*])*\*\)/
    
    NEWLINE: /\\?\r?\n/

    %import common.WORD
    %import common.ESCAPED_STRING
    %import common.CNAME
    %import common.SIGNED_NUMBER
    %import common.INT
    %import common.SIGNED_INT
    %import common.WS

    %ignore WS
    %ignore COMMENT_SLASH
    %ignore COMMENT_BRACE
    %ignore NEWLINE
"""


class Range:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        return "[{}:{}]".format(self.start, self.end)


class Vec:

    def __init__(self, name: str, range: Range):
        self.name = name
        self.range = range

    def __repr__(self):
        return "{}{}".format(self.name, self.range)


# class PortConnection:
#
#     def __init__(self, port_name: str, signal_name: str):
#         self.port_name = port_name
#         self.signal_name = signal_name
#
#     def __repr__(self):
#         return ".{}({})".format(self.port_name, self.signal_name)


class IdentifierIndexed:

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __repr__(self):
        return "{}[{}]".format(self.name, self.index)


class IdentifierSliced:

    def __init__(self, name, range):
        self.name = name
        self.range = range

    def __repr__(self):
        return "{}{}".format(self.name, self.range)


class ModuleInstance:

    def __init__(self, module_name: str, instance_name: str, ports: Dict[str, str]):
        self.module_name = module_name
        self.instance_name = instance_name
        self.ports = ports

    def __repr__(self):
        return "ModuleInstance({}, {}, {})".format(self.module_name, self.instance_name, self.ports)


class NetDeclaration:
    def __init__(self, net_name: str, range: Range):
        self.net_name = net_name
        self.range = range

    def __repr__(self):
        if self.range is not None:
            return "NetDeclaration({} {})".format(self.net_name, self.range)
        else:
            return "NetDeclaration({})".format(self.net_name)


class Module:

    def __init__(self, module_name: str, port_list: List[str], module_items: List):
        self.module_name = module_name
        self.port_list = port_list

        self.module_items = module_items

        self.net_declarations = []
        self.module_instances = []

        for it in module_items:
            if isinstance(it, NetDeclaration):
                self.net_declarations.append(it)
            elif isinstance(it, ModuleInstance):
                self.module_instances.append(it)

            # TODO: also for input_declaration, output_declaration, continuous_assign

    def __repr__(self):
        return "Module({}, {}, {})".format(self.module_name, self.port_list, self.module_items)


class VerilogTransformer(Transformer):
    list_of_ports = list

    @v_args(inline=True)
    def identifier(self, identifier):
        return str(identifier)

    @v_args(inline=True)
    def base(self, base):
        return str(base)[1]

    @v_args(inline=True)
    def identifier_sliced(self, name, range: Range):
        return IdentifierSliced(name, range)

    @v_args(inline=True)
    def identifier_indexed(self, name, index):
        return IdentifierIndexed(name, index)

    @v_args(inline=True)
    def named_port_connection(self, port_name: str, expression):
        return {port_name: expression}

    @v_args(inline=True)
    def assignment(self, left, right):
        return "assignment", left, right

    def list_of_assignments(self, args) -> List:
        return list(args)

    @v_args(inline=True)
    def module(self, module_name, list_of_ports, *module_items):
        # TODO: What happens if list_of_ports is not present?
        items = []
        for it in module_items:
            if isinstance(it, list):
                items.extend(it)
            else:
                items.append(it)

        return Module(module_name, list_of_ports, items)

    @v_args(inline=True)
    def module_instantiation(self, module_name, *module_instances) -> List[ModuleInstance]:
        instances = []
        for module_instance in module_instances:
            instance_name, ports = module_instance
            instances.append(ModuleInstance(module_name, instance_name, ports))

        return instances

    def net_declaration(self, args) -> List[NetDeclaration]:

        if len(args) > 0 and isinstance(args[0], Range):
            _range = args[0]
            variable_names = args[1:]
        else:
            _range = None
            variable_names = args

        declarations = []
        for name in variable_names:
            declarations.append(NetDeclaration(name, _range))
        return declarations

    def list_of_module_connections(self, module_connections):
        connections = dict()
        for conn in module_connections:
            connections.update(**conn)
        return connections

    @v_args(inline=True)
    def module_instance(self, instance_name, module_connections):
        return (instance_name, module_connections)

    @v_args(inline=True)
    def range(self, start, end):
        return Range(start, end)

    @v_args(inline=True)
    def uint(self, s) -> int:
        return int(s)

    @v_args(inline=True)
    def number_explicit_length(self, length, base, mantissa):
        return (length, base, mantissa)

    @v_args(inline=True)
    def number_implicit_length(self, base, mantissa):
        return (base, mantissa)

    @v_args(inline=False)
    def concatenation(self, l):
        result = []
        for x in l:
            if isinstance(x, list):
                result.extend(x)
            else:
                result.append(x)
        return result


def parse_verilog(data: str):
    """
    Parse a string containing data of a verilog file.
    :param data: Raw verilog string.
    :return:
    """
    verilog_parser = Lark(verilog_netlist_grammar,
                          parser='lalr',
                          lexer='standard',
                          transformer=VerilogTransformer()
                          )
    netlist = verilog_parser.parse(data)
    return netlist


def test_parse_verilog1():
    data = r"""
module blabla(port1, port_2);
    input [0:1234] asdf;
    output [1:3] qwer;
    wire [1234:45] mywire;

    assign a = b;

    assign {a, b[1], c[0: 39]} = {x, y[5], z[1:40]};
    assign {a, b[1], c[0: 39]} = {x, y[5], 1'h0 };
    (* asdjfasld ajsewkea 3903na ;lds *)
    wire zero_set;
    OR _blabla_ ( .A(netname), .B (qwer) );
    OR blabla2 ( .A(netname), .B (1'b0) );

wire zero_res;
  (* src = "alu_shift.v:23" *)
  wire zero_set;
  NOT _072_ (
    .A(func_i[2]),
    .Y(_008_)
  );

endmodule
"""

    netlist = parse_verilog(data)
    # print(netlist.pretty())


def test_parse_verilog2():
    from . import test_data

    data = test_data.verilog_netlist()

    netlist = parse_verilog(data)
    print(netlist)
    # print(netlist.pretty())
