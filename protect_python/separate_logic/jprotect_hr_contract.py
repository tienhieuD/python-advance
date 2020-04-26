from xlsxwriter import utility
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.addons.tristar_payroll.models.hr_contract import SALARY_CATEG_SELECTION

X_SALARY_CATEG_SELECTION = SALARY_CATEG_SELECTION + [('90_transfer', 'Tăng cường')]

def jprotect_cm_TristarPayslipSumaryCanteen__compute_salary_categ(self, TristarPayslipSumaryCanteen=None):
    for rec in self:
        if rec.payslip_id.employee_id.department_id != rec.payslip_id.payslip_run_id.dept_id:
            rec.x_salary_categ = '90_transfer'
        else:
            rec.x_salary_categ = rec.payslip_id.employee_id.contract_id.x_salary_categ

        rec.is_foreign_payslip = rec.payslip_id.input('TY_GIA') and rec.payslip_id.input('TY_GIA') != 1.0

def jprotect_cm_TristarPayslipSumaryCanteen__compute_worked_months(self, TristarPayslipSumaryCanteen=None):
    for rec in self:
        if not rec.contract_date_start:
            continue
        today = fields.Date.today()
        diff = relativedelta(rec.contract_date_start, today)
        rec.worked_months = abs(diff.years) * 12 + abs(diff.months)

def jprotect_cm_TristarPayslipSumaryCanteen__compute_summary_salary(self, TristarPayslipSumaryCanteen=None):
    for rec in self:
        rec.current_wage = rec.payslip_id.line("LUONG_CO_BAN_CC")
        rec.responsibility_allowance = rec.payslip_id.line("LUONG_TRACH_NHIEM_CC")
        rec.hot_allowance = rec.payslip_id.line("PHU_CAP_NONG_NUC_CC")

        rec.total_salary = rec.payslip_id.line("TONG_LUONG")
        rec.ot_salary = rec.payslip_id.line("LUONG_TANG_CA")
        rec.responsibility_salary = rec.payslip_id.line("PHU_CAP_TRACH_NHIEM")
        rec.telephone_salary = rec.payslip_id.line("PHU_CAP_DIEN_THOAI")
        rec.position_salary = rec.payslip_id.line("PHU_CAP_VI_TRI_CC")
        rec.night_salary = rec.payslip_id.line("PHU_CAP_LAM_DEM")
        rec.hard_working_salary = rec.payslip_id.line("PHU_CAP_CHUYEN_CAN")
        rec.seniority_salary = rec.payslip_id.line("PHU_CAP_THAM_NIEN_CC")
        rec.eat_and_party_bonus = rec.payslip_id.line("HO_TRO_TIEN_AN_LAM_TIEC_CC")
        rec.holiday_bonus = rec.payslip_id.line("THUONG_LE")
        rec.party_bonus = rec.payslip_id.line("THUONG_TIEC")
        rec.house_rent_salary = rec.payslip_id.line("HO_TRO_NHA_TRO")
        rec.moving_salary = rec.payslip_id.line("HO_TRO_DI_LAI_CC")
        rec.other_salary = rec.payslip_id.line("THU_NHAP_KHAC_CC")

        rec.total = rec.payslip_id.line("TONG_THU_NHAP_CC")

        rec.deduction_social_insurance_salary = rec.payslip_id.line("BHXH_CC")
        rec.deduction_uniform_salary = rec.payslip_id.line("TIEN_DONG_PHUC_CC")
        rec.deduction_other_salary = rec.payslip_id.line("GIAM_TRU_KHAC_CC")
        rec.deduction_total = rec.payslip_id.line("TONG_CAC_KHOAN_GIAM_TRU_CC")

        rec.pit_deductions = rec.payslip_id.line("THUE_TNCN_CAC_KHOAN_GIAM_TRU_CC")
        rec.pit_income = rec.payslip_id.line("THUE_TNCN_THU_NHAP_TINH_THUE_CC")
        rec.pit_salary = rec.payslip_id.line("THUE_TNCN_THUE_TNCN_CC")
        rec.pit_company_support = rec.payslip_id.line("THUE_TNCN_THUE_TNCN_CTY_HO_TRO_CC")
        rec.pit_personal = rec.payslip_id.line("THUE_TNCN_THUE_TNCN_PHAI_NOP_CC")

        rec.real_salary = rec.payslip_id.line("LUONG_THUC_LINH_CC")
        rec.real_salary_usd = rec.real_salary / (rec.payslip_id.input("TY_GIA") or 1.0)

def jprotect_cm_TristarPayslipSumaryCanteen_generate_report(self, **kwargs, TristarPayslipSumaryCanteen=None):
    workbook = super(TristarPayslipSumaryCanteen, self).generate_report(**kwargs)

    if not kwargs.get('tristar_payslip_sumary_canteen'):
        return workbook

    total_line_index = [index for index, row in enumerate(kwargs['data_array']) if not isinstance(row[0], int)]
    if total_line_index:
        begin_row, _ = utility.xl_cell_to_rowcol(kwargs['begin_data_cell'])
        last_col_name = utility.xl_col_to_name(len(kwargs['data_array'][0]) - 1)
        sum_ranges = ['A%s:%s%s' % (begin_row + line_index + 1, last_col_name, begin_row + line_index + 1) for line_index in total_line_index]
        for sr in sum_ranges:
            for cell in workbook.active[sr][0]:
                cell.fill = PatternFill("solid", fgColor="FFDD00")
                cell.font = Font(bold=True)

    sheet = workbook.get_sheet_by_name('DNTT')
    run_id = kwargs.get('run_id')
    if not run_id:
        raise ValidationError(_('Không thể xuất bảng lương, chọn lại bảng lương cần xuất và thử lại.'))
    self.replace_dynamic_values(sheet, kwargs.get('render_values', {}))
    return workbook

def jprotect_cm_TristarPayslipSumaryCanteen__get_line_data(self, seq, s, just_foreign_payslip=False, TristarPayslipSumaryCanteen=None):
    r1 = [
        seq, s.employee_id.name, s.employee_id.identification_id, s.employee_id.x_bank_account_number or None, s.job_id.name, s.contract_date_start, s.worked_months,
        s.social_insurance_wage/1000, s.old_wage/1000, s.current_wage/1000, s.responsibility_allowance/1000, s.telephone_allowance/1000, s.employee_id.contract_id.hot_allowance/1000,
        s.total_day, s.worked_day, s.worked_holiday, s.transfer_workday, s.double_day, s.paid_holiday, s.leave_day, s.night_worked_day, s.ot_day, s.eat_day, s.party_day, s.no_fingerprint_day,
        s.total_salary/1000, s.ot_salary/1000, s.responsibility_salary/1000, s.telephone_salary/1000,
        s.position_salary/1000, s.night_salary/1000, s.hard_working_salary/1000, s.seniority_salary/1000, s.house_rent_salary/1000, s.moving_salary/1000, s.eat_and_party_bonus/1000, s.hot_allowance/1000, s.holiday_bonus/1000, s.party_bonus/1000, s.other_salary/1000,
        s.total/1000,
        s.deduction_social_insurance_salary/1000, s.deduction_other_salary/1000, s.deduction_uniform_salary/1000, s.deduction_total/1000,
        s.pit_deductions/1000, s.pit_income/1000, s.pit_salary/1000, s.pit_company_support/1000, s.pit_personal/1000,
        s.real_salary/1000,]
    r2 = [s.real_salary_usd] if just_foreign_payslip else []
    r3 = [0, 0, s.note or None]
    return r1 + r2 + r3

def jprotect_cm_TristarPayslipSumaryCanteen_export_payslip_run(self, run_id, just_foreign_payslip=False, TristarPayslipSumaryCanteen=None):
    def get_sum_of_row_payslips(rows, skip_cell=2):
        if not rows:
            return []
        result = [0] * len(rows[0])
        for row in rows:
            if not isinstance(row[0], int):
                continue
            for index in range(skip_cell, len(rows[0])):
                if isinstance(row[index], int) or isinstance(row[index], float):
                    result[index] += row[index]
        return [_ or None for _ in result[skip_cell:]]

    if not run_id:
        return

    run = self.env['hr.payslip.run'].browse(run_id)
    summaries = self.search([('run_id', '=', run_id), ('workday_line_id.is_transfer_workday', '=', False)])
    transfer_summaries = self.search([('run_id', '=', run_id), ('workday_line_id.is_transfer_workday', '=', True)])

    if just_foreign_payslip:
        summaries = summaries.filtered('is_foreign_payslip')
        transfer_summaries = transfer_summaries.filtered('is_foreign_payslip')

    rows = []
    payslip_index = 0
    category_index = 0

    for category_value, category_name in dict(SALARY_CATEG_SELECTION).items():
        payslips = summaries.filtered(lambda r: r.x_salary_categ == category_value)

        if not payslips:
            continue

        row_payslips = []
        for payslip in payslips:
            payslip_index += 1
            row_payslips += [self._get_line_data(payslip_index, payslip, just_foreign_payslip)]
        row_category = [chr(category_index + 65), category_name.upper()] + get_sum_of_row_payslips(row_payslips)

        rows += [row_category] + row_payslips
        category_index += 1

    if transfer_summaries:
        row_payslips = []
        for payslip in transfer_summaries:
            row_payslips += [self._get_line_data(payslip_index + 1, payslip, just_foreign_payslip)]
            payslip_index += 1
        row_category = [chr(category_index + 65), "TĂNG CƯỜNG"] + get_sum_of_row_payslips(row_payslips)
        rows += [row_category] + row_payslips

    total_row = [None, "TỔNG CỘNG"] + get_sum_of_row_payslips(rows)
    rows += [total_row]

    file_name = 'Luong T%s.%s.%s.xlsx' % (
        str(run.date_start.month).zfill(2),
        run.date_start.year,
        run.dept_id.name + ('-nuoc-ngoai' if just_foreign_payslip else ''),
    )

    template_file_name = 'bang-luong-foreign.xlsx' if just_foreign_payslip else 'bang-luong.xlsx'
    real_salary_total = sum((summaries | transfer_summaries).mapped('real_salary_usd')) \
        if just_foreign_payslip else round(run.real_salary_total)

    return self.action_report(
        filename=file_name,
        template_file='/tristar_payroll_canteen/static/src/files/%s' % template_file_name,
        begin_data_cell="A10",
        data_array=rows,
        extra_data=None,
        render_values={
            'department': run.dept_id.name,
            'month': run.date_start.month,
            'year': run.date_start.year,
            'norm': run.workday_norms,
            'run': run,
            'person_request': self.env.user,
            'real_salary_total': '{:,}'.format(real_salary_total),
            'today': fields.Date.today(),
            'x_accountant': run.x_accountant,
            'x_hr': run.x_hr,
            'x_director': run.x_director,
        },
        tristar_payslip_sumary_canteen=True,
        run_id=run_id,
    )

def jprotect_cm_TristarPayslipSumaryCanteen_action_view_other_incomes(self, TristarPayslipSumaryCanteen=None):
    self.ensure_one()
    incomes = self.env['salary.income'].search([
        ('employee_id', '=', self.workday_line_id.employee_id.id),
        ('year', '=', self.workday_line_id.workday_year),
        ('month', '=', self.workday_line_id.workday_month)])
    wizard_id = self.env['view.all.incomes.wizard'].create([{
        'income_ids': [(6, 0, incomes.ids)],
        'name': _('Total Other Incomes of %s (%s/%s)') % (
        self.workday_line_id.employee_id.name, self.workday_line_id.workday_month, self.workday_line_id.workday_year),
    }]).id
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'view.all.incomes.wizard',
        'res_id': wizard_id,
        'target': 'new',
        'view_type': 'form',
        'view_mode': 'form',
        'views': [(False, 'form')],
        'context': dict(self._context),
    }