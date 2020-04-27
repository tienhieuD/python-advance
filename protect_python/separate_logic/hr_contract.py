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
        return self.write({'x_status': 'done'})

    def action_payslip_draft(self):
        self.write({'x_status': 'draft'})
        return super(HrPayslip, self).action_payslip_draft()

    def action_payslip_cancel(self):
        return self.write({'x_status': 'draft'})

    @api.multi
    def unlink(self):
        for rec in self:
            employee = rec.employee_id
            month = rec.date_from.month
            year = rec.date_from.year
            tristar_paylip = rec.env['tristar.payslip'].sudo().search([('employee_id', '=', employee.id), ('month', '=', month), ('year', '=', year)])
            tristar_paylip.sudo().unlink()
        if any(rec.x_status == 'done' for rec in self):
            raise ValidationError(_("Không thể xóa phiếu lương đã hoàn thành!"))
        return super(HrPayslip, self).unlink()

    @api.multi
    def get_params(self, key, default=0.0):
        value = self.env['payroll.parameter'].get_value(code=key, department=self.employee_id.department_id)
        return value or default

    @api.multi
    def get_amounts(self, key, default=0.0):
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


    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        for payslip in self:
            year = payslip.date_from.year
            month = payslip.date_from.month
            end_date = monthrange(year, month)[1]
            payslip.date_from = date(year, month, 1)
            payslip.date_to = date(year, month, end_date)
        super(HrPayslip, self).onchange_employee()

    def _compute_total_salary(self):
        categ_receive_real_id = self.env.ref('tristar_payroll.receive_real_categ').id
        read_group_data = self.env['hr.payslip.line'].read_group([
            ('salary_rule_id.category_id', '=', categ_receive_real_id),
            ('slip_id', 'in', self.ids),
        ], fields=['slip_id', 'total'], groupby=['slip_id'])
        data = {gdata['slip_id'][0]: gdata['total'] for gdata in read_group_data}
        for payslip in self:
            payslip.total_salary = data.get(payslip.id, 0)
        # for payslip in self:
            # total_line = payslip.line_ids.sorted(lambda l: l.salary_rule_id.sequence)
            # payslip.total_salary = total_line and total_line[-1].amount or 0.0

    @api.multi
    def line(self, code):
        line = self.line_ids.filtered(lambda l: l.code == code)
        return line and line[0].total or 0

    @api.multi
    def day(self, code):
        worked_days_line = self.worked_days_line_ids.filtered(lambda l: l.code == code)
        return worked_days_line and worked_days_line[0].number_of_days or 0

    @api.multi
    def input(self, code):
        input_line = self.input_line_ids.filtered(lambda l: l.code == code)
        return input_line and input_line[0].amount or 0

    @api.model
    def get_num_of_days(self, employee, field):
        line = self.env['hr.workday.table.line'].search([('employee_id', '=', employee.id)])
        return line and getattr(line[-1], field) or 0.0

    # @api.model
    # def get_amounts(self, employee, field):
    #     return self.get_num_of_days(employee, field)

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        res = super(HrPayslip, self)._get_payslip_lines(contract_ids, payslip_id)
        return res

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        return []

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
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


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    amount = fields.Float(digits=dp.get_precision('Payroll'))

