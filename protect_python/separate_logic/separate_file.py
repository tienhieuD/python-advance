import re


def is_need_to_break(line, current_index=None, all_lines=None, pass_class_method=False):
    return is_import(line) \
           or is_global_variable(line) \
           or is_global_function(line) \
           or (is_class_method(line, current_index, all_lines) if not pass_class_method else False) \
           or is_class(line)


def is_import(line=''):
    return line.startswith('from') or line.startswith('import')


def is_global_variable(line=''):
    return re.match(r'^\w+?\s*?=', line)


def is_global_function(line=''):
    return re.match(r'^def', line)


def is_class_method(line, current_index, lines):
    return re.match(r'^\s{4}def', line) and looking_for_class_of_method(current_index, lines)


def is_class(line=''):
    return re.match(r'^class', line)


def write_import(file, line, current_index, all_lines):
    file.write(line)
    if current_index + 1 >= len(all_lines):
        return
    for next_line in all_lines[current_index + 1:]:
        if is_need_to_break(next_line, current_index, all_lines):
            break
        file.write(next_line)


def write_global_variable(file, line, current_index, all_lines):
    return write_import(file, line, current_index, all_lines)


def write_global_function(file, line, current_index, all_lines):
    file.write(line)
    if current_index + 1 >= len(all_lines):
        return
    for next_line in all_lines[current_index + 1:]:
        if is_need_to_break(next_line, current_index, all_lines, pass_class_method=True):
            break
        file.write(next_line)


def write_class_method(file, line, current_index, all_lines, class_name):
    pattern = r'^    def\s(\w+?)\((.+?),?\s?(\*\w+?)?(,?\s?)(\*\*\w*?)?\):'
    repl = 'def jprotect_cm_{cls_name}_\g<1>(\g<2>, {cls_name}=None, \g<3>\g<4>\g<5>):'.format(cls_name=class_name)
    line = re.sub(pattern, repl, line)
    file.write(line)
    if current_index + 1 >= len(all_lines):
        return
    for next_line in all_lines[current_index + 1:]:
        if is_need_to_break(next_line, current_index, all_lines) or next_line.startswith('    @'):
            break
        next_line = re.sub(r'^\s{4}(.+?)', '\g<1>', next_line)
        if re.match(r'\w+?\s?=\s?fields\..+?\(', next_line)\
                or re.match(r'\s*?#', next_line):
            continue
        file.write(next_line)

def looking_for_class_of_method(current_index, all_lines):
    class_name = None
    for back_line in all_lines[:current_index][::-1]:
        if is_need_to_break(back_line, current_index, all_lines, pass_class_method=True):
            if is_class(back_line):
                class_name = re.match('class\s+?(\w+?)\(', back_line).group(1)
            break
    return class_name


def separate_file(file_path, save_path, main_path):
    with open(file_path, 'r', encoding='utf8') as file:
        lines = file.readlines()

        save_file = open(save_path, 'w', encoding='utf8')
        for index, l in enumerate(lines):
            if is_import(l):
                write_import(save_file, l, index, lines)
            if is_global_variable(l):
                write_global_variable(save_file, l, index, lines)
            if is_global_function(l):
                write_global_function(save_file, l, index, lines)
            if is_class_method(l, index, lines):
                class_name = None
                for back_line in lines[:index][::-1]:
                    if is_need_to_break(back_line, pass_class_method=True):
                        if is_class(back_line):
                            class_name = re.match('class\s+?(\w+?)\(', back_line).group(1)
                        break
                if class_name:
                    write_class_method(save_file, l, index, lines, class_name)
        save_file.close()

        main_file = open(main_path, 'w', encoding='utf8')
        main_file.write('from %s import *\n' % save_path.split('/')[-1].split('.')[0])
        current_index = 0
        while current_index < len(lines)-1:
            l = lines[current_index]
            if is_class_method(l, current_index, lines):
                main_file.write(l)
                class_name = looking_for_class_of_method(current_index=current_index, all_lines=lines)
                if class_name:
                    pattern = r'^    def\s(\w+?)\((.+?),?\s?(\*\w+?)?(,?\s?)(\*\*\w*?)?\):'
                    replace_with = '        return jprotect_cm_{cls_name}_\g<1>(\g<2>, {cls_name}={cls_name}, \g<3>\g<4>\g<5>)'\
                        .format(cls_name=class_name)
                    new_define = re.sub(pattern, replace_with, l)
                    main_file.write(new_define)
                pass_index = 0
                if current_index <= len(lines):
                    for j, next_line in enumerate(lines[current_index+1:], 1):
                        if is_need_to_break(next_line, current_index+j, lines) or next_line.startswith('    @'):
                            break
                        pass_index += 1
                current_index += pass_index
                continue

            main_file.write(l)
            current_index += 1

        main_file.close()


if __name__ == "__main__":
    file_path = 'C:/Users/hieudt/Desktop/python-advance/protect_python/separate_logic/hr_contract.py'
    save_path = 'C:/Users/hieudt/Desktop/python-advance/protect_python/separate_logic/jprotect_hr_contract.py'
    main_path = 'C:/Users/hieudt/Desktop/python-advance/protect_python/separate_logic/main_hr_contract.py'
    separate_file(file_path, save_path, main_path)

    with open('C:/Users/hieudt/Desktop/python-advancexxx/1.py', 'w', encoding='utf8') as file1:
        file1.write('s')

