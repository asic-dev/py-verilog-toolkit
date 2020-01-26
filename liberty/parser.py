##
## Copyright (c) 2019 Thomas Kramer.
## 
## This file is part of liberty-parser 
## (see https://codeberg.org/tok/liberty-parser).
## 
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##
from lark import Lark, Transformer, v_args
from .types import *

liberty_grammar = r"""
    ?start: group
    
    group: name argument_list group_body
    group_body: "{" (statement)* "}"
    
    argument_list: "(" [value ("," value)*] ")"
    
    ?statement: attribute ";"
        | group
        | define ";"
        
    ?value: name
        | number
        | number unit -> number_with_unit
        | numbers
        | string -> escaped_string
        
    numbers: "\"" [number ("," number)*] "\""
        
    unit: CNAME
        
    ?attribute: simple_attribute
        | complex_attribute
        
    simple_attribute: name ":" value
    
    complex_attribute: name argument_list
    
    define: "define" "(" name "," name "," name ")"
    
    name : CNAME
    string: ESCAPED_STRING
    
    number: SIGNED_NUMBER
    
    COMMENT: /\/\*(\*(?!\/)|[^*])*\*\//
    NEWLINE: /\\?\r?\n/
    
    %import common.WORD
    %import common.ESCAPED_STRING
    %import common.CNAME
    %import common.SIGNED_NUMBER
    %import common.WS
    
    %ignore WS
    %ignore COMMENT
    %ignore NEWLINE
"""


@v_args(inline=True)
class LibertyTransformer(Transformer):

    def escaped_string(self, s):
        return EscapedString(s[1:-1].replace('\\"', '"'))

    def string(self, s):
        return s[:]

    def name(self, s):
        return s[:]

    def number(self, s):
        return float(s)

    unit = string
    value = string

    def group_body(self, *args):
        return list(args)

    def number_with_unit(self, num, unit):
        return WithUnit(num, unit)

    def simple_attribute(self, name, value):
        return {name: value}

    def complex_attribute(self, name, arg_list):
        return {name: arg_list}

    def define(self, attribute_name, group_name, attribute_type):
        """

        :param attribute_name:
        :param group_name:
        :param attribute_type: boolean, string, integer or float
        :return:
        """
        return Define(attribute_name, group_name, attribute_type)

        # @v_args(inline=True)
        # def value(self, value):
        #     return value

    def argument_list(self, *args):
        return list(args)

    def group(self, group_name, group_args, body):
        attrs = dict()
        sub_groups = []
        defines = []
        for a in body:
            if isinstance(a, dict):
                attrs.update(a)
            elif isinstance(a, Group):
                sub_groups.append(a)
            elif isinstance(a, Define):
                defines.append(a)
            else:
                print(a)
                assert False

        return Group(group_name, group_args, attrs, sub_groups, defines)


def parse_liberty(data: str) -> Group:
    """
    Parse a string containing data of a liberty file.
    :param data: Raw liberty string.
    :return: `Group` object of library.
    """
    liberty_parser = Lark(liberty_grammar,
                          parser='lalr',
                          lexer='standard',
                          transformer=LibertyTransformer()
                          )
    library = liberty_parser.parse(data)
    return library


def test_parse_liberty1():
    data = r"""
library(test) { 
  time_unit: 1ns;
  string: "asdf";
  mygroup(a, b) {}
  empty() {}
  somegroup(a, b, c) {
    nested_group(d, e) {
        simpleattr_float: 1.2;
    }
  }
  simpleattr_int : 1;
  complexattr(a, b);
  define(myNewAttr, validinthisgroup, float);
}
"""
    library = parse_liberty(data)


def test_parse_liberty2():
    import os.path
    lib_file = os.path.join(os.path.dirname(__file__), '../test_data/gscl45nm.lib')

    data = open(lib_file).read()

    library = parse_liberty(data)

    library_str = str(library)
    open('/tmp/lib.lib', 'w').write(library_str)
    library2 = parse_liberty(library_str)

    cells = library.get_groups('cell')

    invx1 = library.get_group('cell', 'XOR2X1')
    assert invx1 is not None

    pin_y = invx1.get_group('pin', 'Y')
    timings_y = pin_y.get_groups('timing')
    timing_y_a = [g for g in timings_y if g['related_pin'] == 'A'][0]
    assert timing_y_a['related_pin'] == 'A'

    array = timing_y_a.get_group('cell_rise').get_array('values')
    assert array.shape == (6, 6)
