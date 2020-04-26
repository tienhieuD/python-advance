from jprotect_hr_contract import *
from xlsxwriter import utility
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.addons.tristar_payroll.models.hr_contract import SALARY_CATEG_SELECTION

X_SALARY_CATEG_SELECTION = SALARY_CATEG_SELECTION + [('90_transfer', 'Tăng cường')]

class TristarPayslipSumaryCanteen(models.TransientModel):
    _name = 'tristar.payslip.sumary.canteen'
    _inherit = ['xlsx.report.template']
    _description = 'Tristar Payslip Sumary Canteen'

    sequence = fields.Integer()
    run_id = fields.Many2one('hr.payslip.run', required=1, ondelete='cascade')
    payslip_id = fields.Many2one('hr.payslip', ondelete='cascade')
    workday_line_id = fields.Many2one('hr.workday.table.line', ondelete='cascade')
    struct_id = fields.Many2one(related='payslip_id.struct_id', store=1, compute_sudo=True)
    x_salary_categ = fields.Selection(X_SALARY_CATEG_SELECTION, string="Nhóm lương", compute='_compute_salary_categ', store=1, compute_sudo=True)
    is_foreign_payslip = fields.Boolean(compute='_compute_salary_categ', store=1)

    employee_id = fields.Many2one('hr.employee', "Tên nhân viên", related='payslip_id.employee_id', store=1, compute_sudo=True, ondelete='cascade')
    back_account_id = fields.Char(related="employee_id.x_bank_account_number")
    contract_id = fields.Many2one('hr.contract', "Hợp đồng lao động",related='payslip_id.employee_id.contract_id', store=1, compute_sudo=True, ondelete='cascade')
    identification_id = fields.Char("Số CMND", related='payslip_id.employee_id.identification_id', store=1, compute_sudo=True)
    job_id = fields.Many2one('hr.job', "Chức danh công việc", related='payslip_id.employee_id.job_id', store=1, compute_sudo=True)
    contract_date_start = fields.Date("Ngày vào làm", related='payslip_id.employee_id.contract_id.date_start', store=1, compute_sudo=True)
    worked_months = fields.Float("Số tháng làm việc", compute='_compute_worked_months', digits=(16, 0), store=1)
    currency_id = fields.Many2one('res.currency', "Tiền tệ", default=lambda s: s.env.user.company_id.currency_id.id, required=1, store=1, compute_sudo=True)
    social_insurance_wage = fields.Monetary("Mức đóng BHXH (8)", related='payslip_id.employee_id.contract_id.social_insurance_wage', digits=(16, 0), store=1, compute_sudo=True)
    old_wage = fields.Monetary("Mức lương cũ (9)", related='payslip_id.employee_id.contract_id.x_old_wage', digits=(16, 0), store=1, compute_sudo=True)
    current_wage = fields.Monetary("Mức lương hiện tại (10)", compute='_compute_summary_salary', digits=(16, 0), store=1, compute_sudo=True)  #related='payslip_id.employee_id.contract_id.wage', digits=(16, 0), store=1, compute_sudo=True)
    responsibility_allowance = fields.Monetary("Phụ cấp trách nhiệm (11)", compute='_compute_summary_salary', digits=(16, 0), store=1, compute_sudo=True)
    telephone_allowance = fields.Monetary("Phụ cấp điện thoại (12)", related='payslip_id.employee_id.contract_id.telephone_allowance', digits=(16, 0), store=1, compute_sudo=True)

    # workday static
    total_day= fields.Float("Tổng công (14)", related='workday_line_id.total_day', store=1, compute_sudo=True)
    worked_day = fields.Float("Công thực tế (15)", related='workday_line_id.worked_day', store=1, compute_sudo=True)
    worked_holiday = fields.Float("Công lễ đã nhân HS (16)", related='workday_line_id.worked_holiday', store=1, compute_sudo=True)
    transfer_workday = fields.Float("Công tăng cường (17)", related='workday_line_id.transfer_workday', store=1, compute_sudo=True)
    double_day = fields.Float("Công nhân đôi (18)", related='workday_line_id.double_day', store=1, compute_sudo=True)
    paid_holiday = fields.Float("Công nghỉ hưởng lương (19)", related='workday_line_id.paid_holiday', store=1, compute_sudo=True)
    leave_day = fields.Float("Công phép (20)", related='workday_line_id.leave_day', store=1, compute_sudo=True)
    night_worked_day = fields.Float("Công đêm (21)", related='workday_line_id.night_worked_day', store=1, compute_sudo=True)
    ot_day = fields.Float("Công tăng ca (22)", related='workday_line_id.ot_day', store=1, compute_sudo=True)
    eat_day = fields.Float("Công tiền ăn (23)", related='workday_line_id.eat_day', store=1, compute_sudo=True)
    party_day = fields.Float("Công tiệc (24)", related='workday_line_id.party_day', store=1, compute_sudo=True)
    no_fingerprint_day = fields.Float("Khác / Trừ thiếu vân tay (25)", related='workday_line_id.other_no_finger_workday', store=1, compute_sudo=True)

    # salary
    total_salary = fields.Float("Tổng lương (26)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    ot_salary = fields.Float("Tăng ca (27)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    responsibility_salary = fields.Float("Trách nhiệm (28)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    telephone_salary = fields.Float("Điện thoại (29)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))

    position_salary = fields.Float("Vị trí (30)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    night_salary = fields.Float("Làm đêm (31)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    hard_working_salary = fields.Float("Chuyên cần (32)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    seniority_salary = fields.Float("Thâm niên (33)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    # other_income_salary = fields.Float("TN phát sinh", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    house_rent_salary = fields.Float("Nhà trọ (34)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    moving_salary = fields.Float("Đi lại (35)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    eat_and_party_bonus = fields.Float("Hỗ trợ tiền ăn làm tiệc (36)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    hot_allowance = fields.Monetary("Phụ cấp nóng nực (37)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    holiday_bonus = fields.Integer('Thưởng lễ (38)', compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    party_bonus = fields.Integer('Thưởng tiệc (39)', compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    other_salary = fields.Float("TN khác (40)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))

    total = fields.Float("Tổng thu nhập (41)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))

    deduction_social_insurance_salary = fields.Float("Giảm trừ BHXH (42)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    deduction_uniform_salary = fields.Float("Tiền đồng phục (43)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    deduction_other_salary = fields.Float("Giảm trừ khác (44)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    deduction_total = fields.Float("Tổng giảm từ (45)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))

    pit_deductions = fields.Float("Các khoản giảm trừ thuế TNCN (46)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    pit_income = fields.Float("Thu nhập tính thuế (47)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    pit_salary = fields.Float("Thuế TNCN (48)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    pit_company_support = fields.Float("Thuế TNCN Công ty hỗ trợ (49)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    pit_personal = fields.Float("Thuế TNCN phải nộp (50)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))

    real_salary = fields.Float("Thực lĩnh (51)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 0))
    real_salary_usd = fields.Float("Thực lĩnh (quy đổi ngoại tệ)", compute='_compute_summary_salary', store=1, compute_sudo=True, digits=(16, 2))

    note = fields.Text("Ghi chú", related='payslip_id.note')

    @api.depends('payslip_id')
    def _compute_salary_categ(self):
        return jprotect_cm_TristarPayslipSumaryCanteen__compute_salary_categ(self, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )

    @api.depends('contract_date_start')
    def _compute_worked_months(self):
        return jprotect_cm_TristarPayslipSumaryCanteen__compute_worked_months(self, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )

    @api.depends('payslip_id')
    def _compute_summary_salary(self):
        return jprotect_cm_TristarPayslipSumaryCanteen__compute_summary_salary(self, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )

    @api.multi
    def generate_report(self, **kwargs):
        return jprotect_cm_TristarPayslipSumaryCanteen_generate_report(self, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, **kwargs)

    def _get_line_data(self, seq, s, just_foreign_payslip=False):
        return jprotect_cm_TristarPayslipSumaryCanteen__get_line_data(self, seq, s, just_foreign_payslip=False, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )

    @api.model
    def export_payslip_run(self, run_id, just_foreign_payslip=False):
        return jprotect_cm_TristarPayslipSumaryCanteen_export_payslip_run(self, run_id, just_foreign_payslip=False, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )

    @api.multi
    def action_view_other_incomes(self):
        return jprotect_cm_TristarPayslipSumaryCanteen_action_view_other_incomes(self, TristarPayslipSumaryCanteen=TristarPayslipSumaryCanteen, )
