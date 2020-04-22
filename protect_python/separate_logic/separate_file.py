import re
from pprint import pprint as print

CLASS_PATTERN = r'class\s(\w+?)\(.+?\):'
METHOD_PATTERN = r'\s+?def\s(\w+?)\(((.|\n)+?)\):'

def is_class(line):
    return line.startswith('class ')

def is_class_method(line):
    return line.startswith('    def ')

def get_class_name_from_(line):
    return re.match(CLASS_PATTERN, line).groups()[0]

def get_method_name_from_(line):
    return re.match(METHOD_PATTERN, line).groups()[0]

def get_method_params_from_(line):
    str_params = re.match(METHOD_PATTERN, line).groups()[1]
    split_params = str_params.split(',')

def get_method_code(method_name):
    pass

def get_class_names(lines):
    classes = []
    for line in lines:
        if not is_class(line):
            continue
        name = get_class_name_from_(line)
        classes.append(name)
    return classes

class OdooClass(object):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.methods = []
    
    def add_method(self, *method):
        self.method += method

class OdooMethod(object):
    def __init__(self, name, *parameters, code):
        super().__init__(name, *parameters, code=None)
        self.name = name
        self.parameters = parameters
        self.code = code

    def set_code(self, code):
        self.code = code

classes = []
if __name__ == "__main__":
    with open('C:/Users/hieudt/Desktop/advance/protect_python/separate_logic/hr_contract.py', 'r', encoding="utf8") as file:
        lines = file.readlines()

        class_names = get_class_names(lines)
        for cls_name in class_names:
            method_names = 
        for line in lines:
            if is_class(line):
                class_name = get_class_name_from_(line)
                classes.append(OdooClass(class_name))
            if is_class_method(line):
                method_name = get_method_name_from_(line)
                method_params = get_method_params_from_(line)
                method_code = get_method_params_from_(line)
                method = OdooMethod()
                classes[-1].add_method()
        file.close()

