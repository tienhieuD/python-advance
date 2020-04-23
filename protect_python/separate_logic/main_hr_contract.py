from jprotect_hr_contract import *
from odoo import api, fields, models, _


class PayrollParameter(models.Model):
    _name = 'payroll.parameter'
    _description = 'Payroll Parameter'

    department_id = fields.Many2one('hr.department', required=1, ondelete='cascade', index=True)
    name = fields.Char('Mô tả')
    code = fields.Char('Mã', index=True)
    value = fields.Float('Giá trị', digits=(16, 0))

    _sql_constraints = [
        ('code_uniq', 'unique (department_id, code)', _('Phòng ban này tồn tại Đơn giá phụ cấp trùng mã.'))
    ]

    @api.model
    def get_value(self, code, department):
        return jprotect_cm_PayrollParameter_get_value(self, code, department, PayrollParameter):

    @api.model
    def get_default_parameters(self):
        return jprotect_cm_PayrollParameter_get_default_parameters(self, PayrollParameter):
