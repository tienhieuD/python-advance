import openpyxl
from openpyxl import utils
from datetime import datetime
from pprint import pprint
from jinja2 import Template
import re
break_line = '@break-line@'
col = '@col@'
jj = 'jj:'

if __name__ == '__main__':
    wb = openpyxl.load_workbook(filename='template_2.xlsx')
    main_sheet = wb.active

    values = []
    for row in main_sheet.rows:
        row_vals = []
        for cell in row:
            row_vals.append(cell.value)
        values.append(row_vals)
    print(values)

    strs = ""
    for val in values:
        strs += col.join("%s<<%s>>" % (v, type(v).__name__) for v in val)+break_line
    tmpl = Template(strs)
    res = tmpl.render()

    rows = res.split(break_line)
    datas = []
    for r in rows:
        row = r.split(col)
        # if jj in row[0]:
        #     continue
        for cell in row:
            if cell == 'None:':
                cell = None
        datas.append(row)
    print(datas)

    for row in range(len(datas)):
        for col in range(len(datas[row])):
            col_letter = utils.get_column_letter(col+1)
            cell = "%s%s" % (col_letter, row+1)
            value = datas[row][col]
            if re.search(r"<<(.+?)>>", value):
                value_type = re.search(r"<<(.+?)>>", value).group(1)
                value = re.sub(r'<<(.+?)>>', '', value)
                finval = None if value_type == 'NoneType' else eval(value_type)(value)
                main_sheet[cell] = finval

    # main_sheet.insert_rows(48)

#     tmpl = Template(
# """{% for user in [ {'name': 'Hoe' }, {'name': 'Nam'} ] %}
# {{user.name}},
# {% endfor %}""")
#     res = tmpl.render(a=1,b=2)
#     print(res)
#     print(for_start, for_end)
        # for cell in row:
        #     # if not cell.value:
        #     #     continue
        #     # values2.append(cell.value)
        #     if cell.

    # pprint(values1)
    # pprint(values2)
    # pprint(len(values2) == len(values1))

    # main_sheet['B2'] = 200000

    wb.save('export.xlsx')
