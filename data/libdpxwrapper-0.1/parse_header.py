#!/usr/bin/env python
#coding: utf-8

import re

DEBUG = False
CHECK_TYPES = False

re_function_declaration = re.compile("\w+\s+.+\(.+\).*;.*")
re_function_name = re.compile("\w+")
re_function_argtypes = re.compile("(?<=\().+?(?=\))")
re_define_line = re.compile("#define.+")

def parse_file():
    fun_list = []
    def_list = []
    tmp_argtype = []
    for line in open('libdpx.h'):
        found_function = re_function_declaration.match(line.strip())
        if found_function:
            found_line = found_function.group()
            return_type = found_line.split()[0]
            function_name = re_function_name.search(found_line.split()[1]).group()
            argtypes_string = re_function_argtypes.search(found_line).group()
            if DEBUG:
                print '->', found_line.strip()
                print 'function_name', function_name
                print 'return_type', return_type
                print 'argtypes:', argtypes_string

            argtypes_list = []
            for argument in argtypes_string.split(','):
                if len(argument.split()) > 1:
                    argtypes_list.append(' '.join(argument.split()[:-1]))
                    if '*' in argument and not '*' in argtypes_list[-1]:
                        argtypes_list[-1] = argtypes_list[-1] + '*'
                else:
                    argtypes_list.append(argument)

                if CHECK_TYPES:
                    if not argtypes_list[-1] in tmp_argtype:
                        tmp_argtype.append(argtypes_list[-1])

            if DEBUG:
                print 'argtypes_list:', argtypes_list
                print 

            fun_list.append((function_name, argtypes_list, return_type))
        else:
            found_definition = re_define_line.match(line.strip())
            if found_definition:
                found_line = found_definition.group()
                if DEBUG:
                    print '#define ->', found_line
                def_name, def_value = found_line.split()[1:3]
                def_list.append((def_name, def_value))

    if CHECK_TYPES:
        print 'tmp_argtype:', tmp_argtype
    return fun_list, def_list

def get_ctypes_typename(return_type):
    type_map = {'void': 'None', 'int': 'c_int', 'double': 'c_double',
                'unsigned': 'c_uint', 'size_t': 'c_size_t',
                'void*': 'c_void_p', 'unsigned char*': 'POINTER(c_ubyte)',
                'unsigned*': 'POINTER(c_int)', 'double*': 'POINTER(c_double)',
                'int*': 'POINTER(c_int)', 'UInt16*': 'POINTER(c_uint16)'}
    return type_map[return_type]

def write_wrapper(fl):
    fun_list, def_list = parse_file()
    if DEBUG:
        print fun_list
    for function_element in fun_list:
        name = function_element[0]
        argtypes_list = function_element[1]
        return_type = function_element[2]

        fl.write('%s = lib_handle.%s\n' % (name, name))
        fl.write('%s.restype = %s\n' % (name, get_ctypes_typename(return_type)))
        fl.write('%s.argtypes = [%s]\n' % (name, ', '.join([get_ctypes_typename(a) for a in argtypes_list if a != 'void'])))

    for definition in def_list:
        fl.write('%s = %s\n' % definition)


if __name__ == "__main__":
    fl = open("libdpxwrapper.py", 'w')
    fl.write("""\
import platform
from ctypes import *
if platform.system() == 'Windows':
    lib_handle = windll.LoadLibrary("libdpx.dll")
elif platform.system() == 'Linux':
    lib_handle = cdll.LoadLibrary("libdpx.so")
else:
    raise Exception, "your operating system is currently not supported"\n\n""")

    #fl.write("from ctypes import *\n")
    #fl.write("lib_handle = cdll.LoadLibrary('libdpx.so')\n")
    write_wrapper(fl)
    fl.write("""\
DPXREG_VID_CTRL_MODE_C24 = 0x0000
DPXREG_VID_CTRL_MODE_L48 = 0x0001
DPXREG_VID_CTRL_MODE_M16 = 0x0002
DPXREG_VID_CTRL_MODE_C48 = 0x0003\n""")

