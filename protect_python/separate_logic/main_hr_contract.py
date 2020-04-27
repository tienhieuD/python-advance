from jprotect_hr_contract import *
# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
import logging
import functools
_logger = logging.getLogger(__name__)


def hide_zero_value(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs) or ""
    return wrapper


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    x_status = fields.Selection([('draft', 'Nháp'), ('done', 'Hoàn thành')], default='draft', required=1)
    payslip_run_id = fields.Many2one(required=1, ondelete='cascade')
    total_salary = fields.Float(compute='_compute_total_salary', string='Thực lĩnh', digits=(16, 0))

    def x_confirm_payslip(self):
        return jprotect_cm_HrPayslip_x_confirm_payslip(self, HrPayslip=HrPayslip, )

    def action_payslip_draft(self):
        return jprotect_cm_HrPayslip_action_payslip_draft(self, HrPayslip=HrPayslip, )

    def action_payslip_cancel(self):
        return jprotect_cm_HrPayslip_action_payslip_cancel(self, HrPayslip=HrPayslip, )

    @api.multi
    def unlink(self):
        return jprotect_cm_HrPayslip_unlink(self, HrPayslip=HrPayslip, )

    @api.multi
    def get_params(self, key, default=0.0):
        return jprotect_cm_HrPayslip_get_params(self, key, default=0.0, HrPayslip=HrPayslip, )

    @api.multi
    def get_amounts(self, key, default=0.0):
        return jprotect_cm_HrPayslip_get_amounts(self, key, default=0.0, HrPayslip=HrPayslip, )

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        return jprotect_cm_HrPayslip_onchange_employee(self, HrPayslip=HrPayslip, )

    def _compute_total_salary(self):
        return jprotect_cm_HrPayslip__compute_total_salary(self, HrPayslip=HrPayslip, )

    @api.multi
    def line(self, code):
        return jprotect_cm_HrPayslip_line(self, code, HrPayslip=HrPayslip, )

    @api.multi
    def day(self, code):
        return jprotect_cm_HrPayslip_day(self, code, HrPayslip=HrPayslip, )

    @api.multi
    def input(self, code):
        return jprotect_cm_HrPayslip_input(self, code, HrPayslip=HrPayslip, )

    @api.model
    def get_num_of_days(self, employee, field):
        return jprotect_cm_HrPayslip_get_num_of_days(self, employee, field, HrPayslip=HrPayslip, )

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        return jprotect_cm_HrPayslip__get_payslip_lines(self, contract_ids, payslip_id, HrPayslip=HrPayslip, )

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        return jprotect_cm_HrPayslip_get_worked_day_lines(self, contracts, date_from, date_to, HrPayslip=HrPayslip, )

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        return jprotect_cm_HrPayslip_get_inputs(self, contracts, date_from, date_to, HrPayslip=HrPayslip, )

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    amount = fields.Float(digits=dp.get_precision('Payroll'))
