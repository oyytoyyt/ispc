#!/usr/bin/python
#
#  Copyright (c) 2013, Intel Corporation
#  All rights reserved.
# 
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
# 
#    * Neither the name of Intel Corporation nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
# 
# 
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#   IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#   TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#   PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
#   OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# // Author: Filippov Ilia

def print_file(line):
    if options.output != "":
        output = open(options.output, 'w')
        output.writelines(line)
        output.close()

def build_test(commands):
    os.system(commands[4])
    test = os.system(commands[1])
    if options.ref:
        ref = os.system(commands[3])
    return (options.ref and ref) or test

def execute_test(commands):
    r = 0
    common.remove_if_exists(perf_temp+"_test") 
    common.remove_if_exists(perf_temp+"_ref")
    for k in range(int(options.number)):
        r = r + os.system(commands[0])
        if options.ref:
            r = r + os.system(commands[2])
    return r

#gathers all tests results and made an item test from answer structure
def run_test(commands, c1, c2, test, test_ref, b_serial):
    if build_test(commands) != 0:
        error("Compilation fails of test %s\n" % test[0], 0)
        return
    if execute_test(commands) != 0:
        error("Execution fails of test %s\n" % test[0], 0)
        return
    print_debug("TEST COMPILER:\n", s, perf_log)
    analyse_test(c1, c2, test, b_serial, perf_temp+"_test")
    if options.ref:
        print_debug("REFERENCE COMPILER:\n", s, perf_log)
        analyse_test(c1, c2, test_ref, b_serial, perf_temp+"_ref")


def analyse_test(c1, c2, test, b_serial, perf_temp_n):
    tasks = [] #list of results with tasks, it will be test[2]
    ispc = [] #list of results without tasks, it will be test[1]
    absolute_tasks = []  #list of absolute results with tasks, it will be test[4]
    absolute_ispc = [] #list of absolute results without tasks, ut will be test[3]
    serial = [] #list serial times, it will be test[5]
    j = 1
    for line in open(perf_temp_n): # we take test output
        if "speedup" in line: # we are interested only in lines with speedup
            if j == c1: # we are interested only in lines with c1 numbers
                line = line.expandtabs(0)
                line = line.replace("("," ")
                line = line.split(",")
                for i in range(len(line)):
                    subline = line[i].split(" ")
                    number = float(subline[1][:-1])
                    if "speedup from ISPC + tasks" in line[i]:
                        tasks.append(number)
                    else:
                        ispc.append(number)
                c1 = c1 + c2
            j+=1
        if "million cycles" in line:
            if j == c1:
                line = line.replace("]","[")
                line = line.split("[")
                number = float(line[3])
                if "tasks" in line[1]:
                    absolute_tasks.append(number)
                else:
                    if "ispc" in line[1]:
                        absolute_ispc.append(number)
                if "serial" in line[1]:
                    serial.append(number)

    if len(ispc) != 0:
        if len(tasks) != 0:
            print_debug("ISPC speedup / ISPC + tasks speedup / ISPC time / ISPC + tasks time / serial time\n", s, perf_log)
            for i in range(0,len(serial)):
                print_debug("%10s   /\t%10s\t    /%9s  /    %10s\t    /%10s\n" %
                    (ispc[i], tasks[i], absolute_ispc[i], absolute_tasks[i], serial[i]), s, perf_log)
        else:
            print_debug("ISPC speedup / ISPC time / serial time\n", s, perf_log)
            for i in range(0,len(serial)):
                print_debug("%10s   /%9s  /%10s\n" % (ispc[i], absolute_ispc[i], serial[i]), s, perf_log)
    else:
        if len(tasks) != 0:
            print_debug("ISPC + tasks speedup / ISPC + tasks time / serial time\n", s, perf_log)
            for i in range(0,len(serial)):
                print_debug("%10s\t     /    %10s\t /%10s\n" % (tasks[i], absolute_tasks[i], serial[i]), s, perf_log)

    test[1] = test[1] + ispc
    test[2] = test[2] + tasks
    test[3] = test[3] + absolute_ispc
    test[4] = test[4] + absolute_tasks
    if b_serial == True:
        #if we concatenate outputs we should use only the first serial answer.
        test[5] = test[5] + serial

def cpu_get():
    p = open("/proc/stat", 'r')
    cpu = p.readline()
    p.close()
    cpu = cpu.split(" ")
    cpu_usage = (int(cpu[2]) + int(cpu[3]) + int(cpu[4]))
    cpu_all = cpu_usage + int(cpu[5])
    return [cpu_usage, cpu_all]

#returns cpu_usage
def cpu_check():
    if is_windows == False:
        if is_mac == False:
            cpu1 = cpu_get()
            time.sleep(1)
            cpu2 = cpu_get()
            cpu_percent = (float(cpu1[0] - cpu2[0])/float(cpu1[1] - cpu2[1]))*100
        else:
            os.system("sysctl -n vm.loadavg > cpu_temp")
            c = open("cpu_temp", 'r')
            c_line = c.readline()
            c.close
            os.remove("cpu_temp")
            R = c_line.split(' ')
            cpu_percent = float(R[1]) * 3
    else:
	os.system("wmic cpu get loadpercentage /value > cpu_temp")
	c = open("cpu_temp", 'r')
        c_lines = c.readlines()
	c.close()
	os.remove("cpu_temp")
	t = "0"
	for i in c_lines[2]:
            if i.isdigit():
                t = t + i
	cpu_percent = int(t)
    return cpu_percent

#returns geomean of list
def geomean(par):
    temp = 1
    l = len(par)
    for i in range(l):
        temp = temp * par[i]
    temp = temp ** (1.0/l)
    return round(temp, 2)

#takes an answer struct and print it.
#answer struct: list answer contains lists test
#test[0] - name of test
#test[1] - list of results without tasks
#test[2] - list of results with tasks
#test[3] - list of absolute results without tasks
#test[4] - list of absolute results with tasks
#test[5] - list of absolute time without ISPC (serial)
#test[1..4] may be empty
def print_answer(answer):
    filelist = []
    print_debug("--------------------------------------------------------------------------\n", s, perf_log)
    print_debug("test name:\t    ISPC speedup: ISPC + tasks speedup: | " + 
        "ISPC time:    ISPC + tasks time:  serial:\n", s, perf_log)
    filelist.append("test name,ISPC speedup,diff," +
        "ISPC + tasks speedup,diff,ISPC time,diff,ISPC + tasks time,diff,serial,diff\n")
    max_t = [0,0,0,0,0]
    diff_t = [0,0,0,0,0]
    geomean_t = [0,0,0,0,0]
    list_of_max = [[],[],[],[],[]]
    list_of_compare = [[],[],[],[],[],[]]
    for i in range(len(answer)):
        list_of_compare[0].append(answer[i][0])
        for t in range(1,6):
            if len(answer[i][t]) == 0:
                max_t[t-1] = "n/a"
                diff_t[t-1] = "n/a"
                list_of_compare[t].append(0);
            else:
                if t < 3:
                    mm = max(answer[i][t])
                else:
                    mm = min(answer[i][t])
                list_of_compare[t].append(mm)
                max_t[t-1] = '%.2f' % mm
                list_of_max[t-1].append(mm)
                diff_t[t-1] = '%.2f' % (max(answer[i][t]) - min(answer[i][t]))
        print_debug("%s:\n" % answer[i][0], s, perf_log)
        print_debug("\t\tmax:\t%5s\t\t%10s\t|%10s\t%10s\t%10s\n" %
            (max_t[0], max_t[1], max_t[2], max_t[3], max_t[4]), s, perf_log)
        print_debug("\t\tdiff:\t%5s\t\t%10s\t|%10s\t%10s\t%10s\n" %
            (diff_t[0], diff_t[1], diff_t[2], diff_t[3], diff_t[4]), s, perf_log)
        for t in range(0,5):
            if max_t[t] == "n/a":
                max_t[t] = ""
            if diff_t[t] == "n/a":
                diff_t[t] = ""
        filelist.append(answer[i][0] + "," +
                        max_t[0] + "," + diff_t[0] + "," +  max_t[1] + "," + diff_t[1] + "," +
                        max_t[2] + "," + diff_t[2] + "," +  max_t[3] + "," + diff_t[3] + "," +
                        max_t[4] + "," + diff_t[4] + "\n")
    for i in range(0,5):
        geomean_t[i] = geomean(list_of_max[i])
    print_debug("---------------------------------------------------------------------------------\n", s, perf_log)
    print_debug("Geomean:\t\t%5s\t\t%10s\t|%10s\t%10s\t%10s\n" %
        (geomean_t[0], geomean_t[1], geomean_t[2], geomean_t[3], geomean_t[4]), s, perf_log)
    filelist.append("Geomean," + str(geomean_t[0]) + ",," + str(geomean_t[1])
        + ",," + str(geomean_t[2]) + ",," + str(geomean_t[3]) + ",," + str(geomean_t[4]) + "\n")
    print_file(filelist)
    return list_of_compare


def compare(A, B):
    print_debug("\n\n_____________________PERFORMANCE REPORT____________________________\n", False, "")
    print_debug("test name:                 ISPC time: ISPC time ref: %:\n", False, "")
    for i in range(0,len(A[0])):
        if B[3][i] == 0:
            p1 = 0
        else:
            p1 = 100 - 100 * A[3][i]/B[3][i]
        print_debug("%21s:  %10.2f %10.2f %10.2f" % (A[0][i], A[3][i], B[3][i], abs(p1)), False, "")
        if p1 < -1:
            print_debug(" <+", False, "")
        if p1 > 1:
            print_debug(" <-", False, "")
        print_debug("\n", False, "")
    print_debug("\n", False, "")

    print_debug("test name:                 TASKS time: TASKS time ref: %:\n", False, "")
    for i in range(0,len(A[0])):
        if B[4][i] == 0:
            p2 = 0
        else:
            p2 = 100 - 100 * A[4][i]/B[4][i]
        print_debug("%21s:  %10.2f %10.2f %10.2f" % (A[0][i], A[4][i], B[4][i], abs(p2)), False, "")
        if p2 < -1:
            print_debug(" <+", False, "")
        if p2 > 1:
            print_debug(" <-", False, "")
        print_debug("\n", False, "")
    if "performance.log" in options.in_file:
        print_debug("\n\n_________________Watch performance.log for details________________\n", False, "")
    else:
        print_debug("\n\n__________________________________________________________________\n", False, "")



def perf(options1, args):
    global options
    options = options1  
    global s
    s = options.silent

    # save current OS
    global is_windows
    is_windows = (platform.system() == 'Windows' or
              'CYGWIN_NT' in platform.system())
    global is_mac
    is_mac = (platform.system() == 'Darwin')

    # save current path
    pwd = os.getcwd()
    pwd = pwd + os.sep
    pwd1 = pwd
    if is_windows:
        pwd1 = "..\\..\\"

    # check if cpu usage is low now
    cpu_percent = cpu_check()
    if cpu_percent > 20:
        error("CPU Usage is very high.\nClose other applications.\n", 2)

    global ispc_test
    global ispc_ref
    global ref_compiler
    global refc_compiler
    # check that required compilers exist
    PATH_dir = string.split(os.getenv("PATH"), os.pathsep)
    ispc_test_exists = False
    ispc_ref_exists = False
    ref_compiler_exists = False
    if is_windows == False:
        ispc_test = "ispc"
        ref_compiler = "g++"
        refc_compiler = "gcc"
        if options.compiler != "":
            if options.compiler == "clang" or options.compiler == "clang++":
                ref_compiler = "clang++"
                refc_compiler = "clang"
            if options.compiler == "icc" or options.compiler == "icpc":
                ref_compiler = "icpc"
                refc_compiler = "icc"
    else:
        ispc_test = "ispc.exe"
        ref_compiler = "cl.exe"
    ispc_ref = options.ref
    if options.ref != "":
        options.ref = True
    for counter in PATH_dir:
        if os.path.exists(counter + os.sep + ispc_test):
            ispc_test_exists = True
        if os.path.exists(counter + os.sep + ref_compiler):
            ref_compiler_exists = True
        if os.path.exists(counter + os.sep + ispc_ref):
            ispc_ref_exists = True
    if not ispc_test_exists:
        error("ISPC compiler not found.\nAdded path to ispc compiler to your PATH variable.\n", 1)
    if not ref_compiler_exists:
        error("C/C++ compiler %s not found.\nAdded path to %s compiler to your PATH variable.\n" % (ref_compiler, ref_compiler), 1)
    if options.ref:
        if not ispc_ref_exists:
            error("ISPC reference compiler not found.\nAdded path to ispc reference compiler to your PATH variable.\n", 1)

    # checks that config file exists
    path_config = os.path.normpath(options.config)
    if os.path.exists(path_config) == False:
        error("config file not found: %s.\nSet path to your config file in --config.\n" % options.config, 1)
        sys.exit()

    # read lines from config file except comments
    f = open(path_config, 'r')
    f_lines = f.readlines()
    f.close()
    lines =[]
    for i in range(len(f_lines)):
        if f_lines[i][0] != "%":
            lines.append(f_lines[i])
    length = len(lines)

    # prepare build.log, perf_temp and perf.log files
    global perf_log
    if options.in_file:
        perf_log = pwd + options.in_file
        common.remove_if_exists(perf_log)
    else:
        perf_log = ""
    global build_log
    build_log = pwd + os.sep + "logs" + os.sep + "perf_build.log"
    common.remove_if_exists(build_log)
    if os.path.exists(pwd + os.sep + "logs") == False:
        os.makedirs(pwd + os.sep + "logs")

    global perf_temp
    perf_temp = pwd + "perf_temp"
    # end of preparations
 
    print_debug("Okey go go go!\n\n", s, perf_log)
    
    #print compilers versions   
    common.print_version(ispc_test, ispc_ref, ref_compiler, False, perf_log, is_windows) 

    # begin
    i = 0
    answer = []
    answer_ref = []

    # loop for all tests
    while i < length-2:
        # we read name of test
        print_debug("%s" % lines[i], s, perf_log)
        test = [lines[i][:-1],[],[],[],[],[]]
        test_ref = [lines[i][:-1],[],[],[],[],[]]
        # read location of test
        folder = lines[i+1]
        folder = folder[:-1]
        folder = os.path.normpath(options.path + os.sep + "examples" + os.sep + folder)
        # check that test exists
        if os.path.exists(folder) == False:
            error("Can't find test %s. Your path is: \"%s\".\nChange current location to ISPC_HOME or set path to ISPC_HOME in --path.\n" %
                 (lines[i][:-1], options.path), 1)
        os.chdir(folder)
        # read parameters of test
        command = lines[i+2]
        command = command[:-1]
        if is_windows == False:
            ex_command_ref = "./ref " + command + " >> " + perf_temp + "_ref"
            ex_command = "./test " + command + " >> " + perf_temp + "_test"
            bu_command_ref = "make CXX="+ref_compiler+" CC="+refc_compiler+ " EXAMPLE=ref ISPC="+ispc_ref+" >> "+build_log+" 2>> "+build_log
            bu_command = "make CXX="+ref_compiler+" CC="+refc_compiler+ " EXAMPLE=test ISPC="+ispc_test+" >> "+build_log+" 2>> "+build_log
            re_command = "make clean >> "+build_log
        else:
            ex_command_ref = "x64\\Release\\ref.exe " + command + " >> " + perf_temp + "_ref"
            ex_command = "x64\\Release\\test.exe " + command + " >> " + perf_temp + "_test"
            bu_command_ref = "msbuild /V:m /p:Platform=x64 /p:Configuration=Release /p:TargetDir=.\ /p:TargetName=ref /t:rebuild >> " + build_log
            bu_command = "msbuild /V:m /p:Platform=x64 /p:Configuration=Release /p:TargetDir=.\ /p:TargetName=test /t:rebuild >> " + build_log
            re_command = "msbuild /t:clean >> " + build_log
        commands = [ex_command, bu_command, ex_command_ref, bu_command_ref, re_command]
        # parsing config parameters
        next_line = lines[i+3]
        if next_line[0] == "!": # we should take only one part of test output
            R = next_line.split(' ')
            c1 = int(R[1]) #c1 is a number of string which we want to use in test output
            c2 = int(R[2]) #c2 is total number of strings in test output
            i = i+1
        else:
            c1 = 1
            c2 = 1
        next_line = lines[i+3]
        if next_line[0] == "^":  #we should concatenate result of this test with previous one
            run_test(commands, c1, c2, answer[len(answer)-1], answer_ref[len(answer)-1], False)
            i = i+1
        else: #we run this test and append it's result to answer structure
            run_test(commands, c1, c2, test, test_ref, True)
            answer.append(test)
            answer_ref.append(test_ref)

        # preparing next loop iteration
        os.chdir(pwd1)
        i+=4

    # delete temp file
    common.remove_if_exists(perf_temp+"_test")
    common.remove_if_exists(perf_temp+"_ref")

    #print collected answer
    print_debug("\n\nTEST COMPILER:\n", s, perf_log)
    A = print_answer(answer)
    if options.ref != "":
        print_debug("\n\nREFERENCE COMPILER:\n", s, perf_log)
        B = print_answer(answer_ref)
        # print perf report
        compare(A,B)

 

###Main###
from optparse import OptionParser
import sys
import os
import operator
import time
import glob
import string
import platform
# our functions
import common
print_debug = common.print_debug
error = common.error

if __name__ == "__main__":
    # parsing options
    parser = OptionParser()
    parser.add_option('-n', '--number', dest='number',
        help='number of repeats', default="3")
    parser.add_option('-c', '--config', dest='config',
        help='config file of tests', default="./perf.ini")
    parser.add_option('-p', '--path', dest='path',
        help='path to test_system directory', default=".")
    parser.add_option('-s', '--silent', dest='silent',
        help='silent mode, only table output', default=False, action="store_true")
    parser.add_option('-o', '--output', dest='output',
        help='output file for script reading', default="")
    parser.add_option('--compiler', dest='compiler',
        help='C/C++ compiler', default="")
    parser.add_option('-r', '--ref', dest='ref',
        help='set reference compiler for compare', default="")
    parser.add_option('-f', '--file', dest='in_file',
        help='file to save perf output', default="")
    (options, args) = parser.parse_args()
    perf(options, args)
