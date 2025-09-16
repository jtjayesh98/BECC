import pandas as pd
import math
import sys 
if len(sys.argv) > 1:
    sample_area = sys.argv[1]
    district_name = sys.argv[2]
    state_name = sys.argv[3]
else:
    sample_area = "Pangatira"
    district_name = "Dhenkanal"
    state_name = "Odisha"



def process(process_stack):
    if process_stack[0] == "NUM":
        number = ""
        for i in process_stack[1:]:
            number += i
        number = float(number)
    else:
        number = ""
        for i in process_stack[1:]:
            number += i
    return (number, process_stack[0])







def produce_stack(equations):
    process_stack = []
    num_stack = []
    variable_stack = []
    operation_stack = []
    garbage_stack = []
    final_stack = []
    ite = 0
    alpha = False
    numeric = False
    for eq in equations:
        if ite == len(equations) - 1:
            if len(process_stack) != 0:
                value, stack_name = process(process_stack) 
                process_stack = []
                alpha = False
                numeric = False
                if stack_name == "OPER":
                    operation_stack.append(value)
                else:
                    variable_stack.append(value)
                final_stack.append(value)               
        elif alpha == True and (eq.isnumeric() or (eq in ["*", "^", "+", "-"]) or (eq in ["(", ")"])):
            value, stack_name = process(process_stack)
            process_stack = []
            alpha = False
            if stack_name == "OPER":
                operation_stack.append(value)
            else:
                variable_stack.append(value)
            final_stack.append(value)  
        elif numeric == True and (eq.isalpha() or (eq in ["*", "^", "+", "-"]) or (eq in ["(", ")"])):
            value, stack_name = process(process_stack)
            process_stack = []
            numeric = False
            if stack_name == "OPER":
                operation_stack.append(value)
            else:
                variable_stack.append(value)
            final_stack.append(value)  
        if eq.isnumeric() or eq == ".":
            if len(process_stack) == 0:
                process_stack.append("NUM")
                numeric = True 
            process_stack.append(eq)
        elif eq in ["*", "^", "+", "-", "/", "(", ")"]:
            if eq not in ["(", ")"]:
                operation_stack.append(eq)
            final_stack.append(eq)              
        elif eq.isalpha():
            if eq in ["X", "Z", "Y"]:
                variable_stack.append(eq)
                final_stack.append(eq)  
            else:
                if len(process_stack) == 0:
                    process_stack.append("OPER")
                    alpha = True
                process_stack.append(eq)
        # elif eq in ["(", ")"]:
        #     continue

        ite += 1

    return final_stack

import math

def single_calculation(sing_cal):
    print(sing_cal)
    if sing_cal[1] == "*":
        return sing_cal[0]*sing_cal[2]
    elif sing_cal[1] == "/":
        return sing_cal[0]/sing_cal[2]
    elif sing_cal[1] == "^":
        return math.pow(sing_cal[0], sing_cal[2])
    elif sing_cal[0] == "log" or sing_cal[0] == "log":
        return math.log(sing_cal[1], 10)
    elif sing_cal[0] == "exp":
        return math.exp(sing_cal[1])
    elif sing_cal[0] == "sqrt":
        return math.sqrt(sing_cal[1])
    elif sing_cal[1] == "+":
        return sing_cal[0]+sing_cal[2]
    elif sing_cal[1] == "-":
        return sing_cal[0]-sing_cal[2]

def calculate(prod_stack):
    val = 0
    if len(prod_stack) == 1:
        return prod_stack[0]
    while len(prod_stack) > 1:
        sing_cal = []
        ite = 0
        new_flag = False
        curr_stack = []
        flag = False
        if len(prod_stack) == 3:
            curr_stack = [single_calculation(prod_stack)]
        else:
            for i in prod_stack:
                if ("*" in prod_stack) or ("log" in prod_stack) or ("sqrt" in prod_stack) or ("ln" in prod_stack) or ("/" in prod_stack) or ("^" in prod_stack) or ("exp" in prod_stack):
                    if flag == True:
                        sing_cal.append(i)
                        flag = False
                        curr_stack.append(single_calculation(sing_cal))
                        sing_cal = []
                    elif i in ["log", "ln", "sqrt", "exp"]:
                        sing_cal.append(i)
                        flag = True                    
                    elif i in ["*", "^", "/"]:
                        var1 = curr_stack.pop(-1)
                        sing_cal.append(var1)
                        sing_cal.append(i)
                        flag = True

                    else:
                        curr_stack.append(i)

                else:
                    if len(sing_cal) == 3:
                        curr_stack.append(single_calculation(sing_cal))
                        sing_cal = []
                        new_flag = True
                        curr_stack.append(i)
                    else:
                        if new_flag == False:
                            sing_cal.append(i)
                        else:
                            curr_stack.append(i)
        prod_stack = curr_stack
    return prod_stack[0]
            


def collapse(stack):
    new_stack = []
    while "(" in stack or ")" in stack:
        new_stack = []
        prod_stack = []
        flag = False
        for st in stack:
            if flag == False:
                if st == "(":
                    flag = True
                else:
                    new_stack.append(st)
            else:
                if st == "(":                    
                    new_stack.append("(")
                    new_stack = new_stack + prod_stack
                    prod_stack = []
                elif st == ")":
                    flag = False
                    new_stack.append(calculate(prod_stack))
                else:
                    prod_stack.append(st)
        
        stack = new_stack
    return stack


def ret_funct(prod_stack):
    if prod_stack[0] == "log":
        return ""

def collapse2(stack):
    new_stack = []


    ite = 0
    check = 0
    for i in stack:
        if check%3 != 0:
            check += 1
            ite += 1
            continue
        if i == "log":
            new_stack.append("math.log10")
        elif i == "ln":
            new_stack.append("math.log")
        elif i == "sqrt":
            new_stack.append("math.sqrt")
        elif i == "^":
            new_stack.append("**")
        elif i == "exp":
            new_stack.append("math.exp")

        # elif i == "(" and isinstance(stack[ite+1], float) and stack[ite+2] == ")":
        #     new_stack.append(int(stack[ite + 1]))
        #     check += 1
        else:
            new_stack.append(i)
        ite += 1

    return new_stack

def add_String(stack):
    outStr = ""
    for i in stack:
        outStr += str(i)
    return outStr           
                



def eval2(file, final_stack, j):
    if "W" in final_stack:
        return "math.exp(2.53*math.log(" + str(float(file["DBH"].iloc[j]))  + ")-2.134)"
    ite = 0
    new_stack = []
    neg_stack = ""
    flag = False
    for i in final_stack:
        if i == "X":
            if file["Unit_X"].iloc[j] == "m":
                new_stack.append(float(file["DBH"].iloc[j])/100)
            elif file["Unit_X"].iloc[j] == "cm":
                new_stack.append(float(file["DBH"].iloc[j]))
        elif i == "Z":
            new_stack.append(float(file["Height"].iloc[j]))
        elif i == "-":
            if final_stack[ite-1] == "(":
                flag = True
                val = new_stack.pop(-1)
                neg_stack += i
            else:
                new_stack.append("-")
        elif flag:
            if i == ")" or not isinstance(i, float):
                flag = False
                new_stack.append("(")
                new_stack.append(float(neg_stack))
                neg_stack = ""
                new_stack.append(i)
            else:
                if isinstance(i, float):
                    neg_stack += str(i)
        else:
            new_stack.append(i)
        ite += 1
    final_stack = new_stack
    # print(add_String(collapse2(final_stack)))
    return add_String(collapse2(final_stack))

# calculate([199.2222, '*', 6.684507609859605, '^', 2.0, '+', 263.1915, '*', 6.684507609859605, '-', 9.913])

# def add_variable(stack):



# file = pd.read_csv("./ADHAPALI_allometric.csv")

# equations = file["Equation"]


# biomass = []

# for i in range(len(file)):
#     print(i)
#     print(file['Equation'].iloc[i])
#     eq = produce_stack(file["Equation"].iloc[i])
#     # print(eq)
#     string = eval2(eq, i)
#     try:
#         if eval(string) > 0:
#             biomass.append(eval(string))
#         else:
#             biomass.append(eval("math.exp(2.53*math.log(" + str(float(file["DBH"].iloc[i]))  + ")-2.134)"))
#     except KeyError:
#         print("Invalid input. Please enter a valid number.")
# file["Calc Biomass"] = biomass
# file.to_csv("./ADHAPALI_biomass.csv", index=False)
# print("Biomass calculation completed and saved to ADHAPALI_biomass.csv")




def biomass_calculation(area):
    file = pd.read_csv(f"./data/GEE_exports_{district_name}/" + area.upper() + "_allometric.csv")
    equations = file["Equation"]
    biomass = []
    for i in range(len(file)):
        eq = produce_stack(file["Equation"].iloc[i])
        # print(eq)
        string = eval2(file, eq, i)
        try:
            if eval(string) > 0:
                biomass.append(eval(string))
            else:
                biomass.append(eval("math.exp(2.53*math.log(" + str(float(file["DBH"].iloc[i]))  + ")-2.134)"))
        except KeyError:
            print("Invalid input. Please enter a valid number.")
    file["Total biomass"] = biomass
    file.to_csv(f"./data/GEE_exports_{district_name}/" + area.upper() + "_biomass.csv", index=False)
    print("Biomass calculation completed and saved to " + area + "_biomass.csv")

import os

if os.path.exists(f'./data/GEE_exports_{district_name}/{sample_area.upper()}_allometric.csv'):
    biomass_calculation(sample_area)
else:
    print("Please Upload the Allometric file to the Data Folder")