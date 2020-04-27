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


def jprotect_cm_HrPayslip_x_confirm_payslip(self, HrPayslip=None, ):
    return self.write({'x_status': 'done'})

def jprotect_cm_HrPayslip_action_payslip_draft(self, HrPayslip=None, ):
    self.write({'x_status': 'draft'})
    return super(HrPayslip, self).action_payslip_draft()

def jprotect_cm_HrPayslip_action_payslip_cancel(self, HrPayslip=None, ):
    return self.write({'x_status': 'draft'})

def jprotect_cm_HrPayslip_unlink(self, HrPayslip=None, ):
    for rec in self:
        employee = rec.employee_id
        month = rec.date_from.month
        year = rec.date_from.year
        tristar_paylip = rec.env['tristar.payslip'].sudo().search([('employee_id', '=', employee.id), ('month', '=', month), ('year', '=', year)])
        tristar_paylip.sudo().unlink()
    if any(rec.x_status == 'done' for rec in self):
        raise ValidationError(_("Không thể xóa phiếu lương đã hoàn thành!"))
    return super(HrPayslip, self).unlink()

def jprotect_cm_HrPayslip_get_params(self, key, default=0.0, HrPayslip=None, ):
    value = self.env['payroll.parameter'].get_value(code=key, department=self.employee_id.department_id)
    return value or default

def jprotect_cm_HrPayslip_get_amounts(self, key, default=0.0, HrPayslip=None, ):
    self.ensure_one()
    get_allowance_amount = self.env['salary.allowance'].sudo().get_allowance_amount

    is_office = self.employee_id.department_id.is_department_office()
    model = is_office and 'hr.workday.office.line' or 'hr.workday.table.line'
    workday_line = self.env[model].search([
        ('workday_month', '=', self.date_from.month),
        ('workday_year', '=', self.date_from.year),
        ('employee_id', '=', self.employee_id.id),
        ('state', '=', 'confirmed'),
    ], limit=1)
    amount = key in workday_line.fields_get_keys() and workday_line[key] \
             or get_allowance_amount(self.employee_id, key)
    return amount or default


def jprotect_cm_HrPayslip_onchange_employee(self, HrPayslip=None, ):
    for payslip in self:
        year = payslip.date_from.year
        month = payslip.date_from.month
        end_date = monthrange(year, month)[1]
        payslip.date_from = date(year, month, 1)
        payslip.date_to = date(year, month, end_date)
    super(HrPayslip, self).onchange_employee()

def jprotect_cm_HrPayslip__compute_total_salary(self, HrPayslip=None, ):
    categ_receive_real_id = self.env.ref('tristar_payroll.receive_real_categ').id
    read_group_data = self.env['hr.payslip.line'].read_group([
        ('salary_rule_id.category_id', '=', categ_receive_real_id),
        ('slip_id', 'in', self.ids),
    ], fields=['slip_id', 'total'], groupby=['slip_id'])
    data = {gdata['slip_id'][0]: gdata['total'] for gdata in read_group_data}
    for payslip in self:
        payslip.total_salary = data.get(payslip.id, 0)

def jprotect_cm_HrPayslip_line(self, code, HrPayslip=None, ):
    line = self.line_ids.filtered(lambda l: l.code == code)
    return line and line[0].total or 0

def jprotect_cm_HrPayslip_day(self, code, HrPayslip=None, ):
    worked_days_line = self.worked_days_line_ids.filtered(lambda l: l.code == code)
    return worked_days_line and worked_days_line[0].number_of_days or 0

def jprotect_cm_HrPayslip_input(self, code, HrPayslip=None, ):
    input_line = self.input_line_ids.filtered(lambda l: l.code == code)
    return input_line and input_line[0].amount or 0

def jprotect_cm_HrPayslip_get_num_of_days(self, employee, field, HrPayslip=None, ):
    line = self.env['hr.workday.table.line'].search([('employee_id', '=', employee.id)])
    return line and getattr(line[-1], field) or 0.0


def jprotect_cm_HrPayslip__get_payslip_lines(self, contract_ids, payslip_id, HrPayslip=None, ):
    res = super(HrPayslip, self)._get_payslip_lines(contract_ids, payslip_id)
    return res

def jprotect_cm_HrPayslip_get_worked_day_lines(self, contracts, date_from, date_to, HrPayslip=None, ):
    return []

def jprotect_cm_HrPayslip_get_inputs(self, contracts, date_from, date_to, HrPayslip=None, ):
    res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)

    rates = self._context.get('rate_ids')
    advance_run = self._context.get('advance_run')

    for contract in contracts:
        if rates:
            ex_rate = rates.filtered(lambda r: r.currency_id == contract.x_payroll_currency_id).mapped('value')
            res += [{'name': _("Tỷ giá"), 'code': "TY_GIA", 'contract_id': contract.id, 'amount': ex_rate and ex_rate[0] or 1.0}]
        if advance_run:
            advance_payslip = self.search([('payslip_run_id', '=', advance_run.id), ('employee_id', '=', contract.employee_id.id)], limit=1)
            res += [{'name': _("Tạm ứng"), 'code': "TAM_UNG", 'contract_id': contract.id, 'amount': advance_payslip.total_salary}]

    return res


