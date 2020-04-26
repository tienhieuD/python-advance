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
        for rec in self:
            if rec.payslip_id.employee_id.department_id != rec.payslip_id.payslip_run_id.dept_id:
                rec.x_salary_categ = '90_transfer'
            else:
                rec.x_salary_categ = rec.payslip_id.employee_id.contract_id.x_salary_categ

            rec.is_foreign_payslip = rec.payslip_id.input('TY_GIA') and rec.payslip_id.input('TY_GIA') != 1.0

    @api.depends('contract_date_start')
    def _compute_worked_months(self):
        for rec in self:
            if not rec.contract_date_start:
                continue
            today = fields.Date.today()
            diff = relativedelta(rec.contract_date_start, today)
            rec.worked_months = abs(diff.years) * 12 + abs(diff.months)

    @api.depends('payslip_id')
    def _compute_summary_salary(self):
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

    @api.multi
    def generate_report(self, **kwargs):
        workbook = super(TristarPayslipSumaryCanteen, self).generate_report(**kwargs)

        if not kwargs.get('tristar_payslip_sumary_canteen'):
            return workbook

        # Fill color total lines
        total_line_index = [index for index, row in enumerate(kwargs['data_array']) if not isinstance(row[0], int)]
        if total_line_index:
            begin_row, _ = utility.xl_cell_to_rowcol(kwargs['begin_data_cell'])
            last_col_name = utility.xl_col_to_name(len(kwargs['data_array'][0]) - 1)
            sum_ranges = ['A%s:%s%s' % (begin_row + line_index + 1, last_col_name, begin_row + line_index + 1) for line_index in total_line_index]
            for sr in sum_ranges:
                for cell in workbook.active[sr][0]:
                    cell.fill = PatternFill("solid", fgColor="FFDD00")
                    cell.font = Font(bold=True)

        # ADD SHEET DNTT
        sheet = workbook.get_sheet_by_name('DNTT')
        run_id = kwargs.get('run_id')
        if not run_id:
            raise ValidationError(_('Không thể xuất bảng lương, chọn lại bảng lương cần xuất và thử lại.'))
        self.replace_dynamic_values(sheet, kwargs.get('render_values', {}))
        return workbook

    def _get_line_data(self, seq, s, just_foreign_payslip=False):
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

    @api.model
    def export_payslip_run(self, run_id, just_foreign_payslip=False):
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
        # rate = (run.rate_ids and run.rate_ids[0].value or 1.0) if just_foreign_payslip else 1.0
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

    @api.multi
    def action_view_other_incomes(self):
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
            # 'name': _('View Incomes'),
            'type': 'ir.actions.act_window',
            'res_model': 'view.all.incomes.wizard',
            'res_id': wizard_id,
            'target': 'new',
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': self.env.ref('tristar_payroll_canteen.salary_income_tree').id,
            'views': [(False, 'form')],
            'context': dict(self._context),
        }