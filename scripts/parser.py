import pandas as pd
import math
import sys 
import math

import os
'''
Establishing Global Parameters
------------------------------
sample_area: Name of the sampling area
district_name: Name of the district
state_name: Name of the state
'''

if len(sys.argv) > 1:
    sample_area = sys.argv[1]
    district_name = sys.argv[2]
    state_name = sys.argv[3]
else:
    sample_area = "Pangatira"
    district_name = "Dhenkanal"
    state_name = "Odisha"





def process(process_stack):
    '''
    Function to process the current stack and return the value and its type.
    Args:
        process_stack: List of strings representing the current stack.
    Returns:
        Tuple containing the processed value and its type ("NUM" or "OPER").
    '''
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
    '''
    Function to convert an equation string into a stack of tokens.
    Args:
        equations: String representing the equation.
    Returns:
        List of tokens representing the equation.
    '''
    process_stack = []
    variable_stack = []
    operation_stack = []
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
        ite += 1
    return final_stack


            
def collapse2(stack):
    '''
    Function to collapse the stack by replacing certain tokens with their corresponding Python functions.
    Args:
        stack: List of tokens representing the equation.
    Returns:
        List of tokens with certain tokens replaced by Python functions.
    '''
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
        else:
            new_stack.append(i)
        ite += 1
    return new_stack

def add_String(stack):
    '''
    Function to convert a list of tokens into a single string.
    Args:
        stack: List of tokens.
    Returns:
        String representation of the tokens.
    '''
    outStr = ""
    for i in stack:
        outStr += str(i)
    return outStr           
                



def eval2(file, final_stack, j):
    '''
    Function to evaluate the final stack and return a string representation of the equation.
    Args:
        file: DataFrame containing the variables and their values.
        final_stack: List of tokens representing the equation.
        j: Index of the current row in the DataFrame.
    Returns:
        String representation of the evaluated equation.
    '''
    
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
    return add_String(collapse2(final_stack))



def biomass_calculation(area):
    '''
    Function to calculate biomass based on allometric equations.
    Args:
        area: Name of the sampling area.
    '''
    
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



if os.path.exists(f'./data/GEE_exports_{district_name}/{sample_area.upper()}_allometric.csv'):
    biomass_calculation(sample_area)
else:
    print("Please Upload the Allometric file to the Data Folder")