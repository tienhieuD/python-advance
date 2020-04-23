from odoo import api, fields, models, _


def jprotect_cm_PayrollParameter_get_value(self, code, department, PayrollParameter):
    param = self.search([('code', '=', code), ('department_id', '=', department.id)], limit=1)
    return param.value

def jprotect_cm_PayrollParameter_get_default_parameters(self, PayrollParameter):
    keys = ('name', 'code', 'value')
    vals = [
        ('Phụ cấp làm đêm (nhân viên Bếp)',     'LD1',      20000),
        ('Phụ cấp làm đêm (nhân viên Kế toán)', 'LD2',      10000),
        ('Phụ cấp chuyên cần (mức 1)',          'CC1',      100000),
        ('Phụ cấp chuyên cần (mức 2)',          'CC2',      50000),
        ('Phụ cấp thâm niên tối đa',            'TN1',      250000),
        ('Phụ cấp thâm niên (mỗi năm)',         'TN2',      50000),
        ('Hỗ trợ nhà trọ',                      'NT1',      200000),
        ('Hỗ trợ tiền ăn',                      'ALT1',     20000),
        ('Hỗ trợ làm tiệc',                     'ALT2',     75000),
        ('Thưởng tiệc 3',                       'LT3',      100000),
        ('Thưởng tiệc 2',                       'LT2',      70000),
        ('Thưởng tiệc 1',                       'LT1',      50000),
        ('Hỗ trợ đi lại (đơn giá)',             'DL',       10000),
    ]
    return [(0, 0, dict(zip(keys, val))) for val in vals]