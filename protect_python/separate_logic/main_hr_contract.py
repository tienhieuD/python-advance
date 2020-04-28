from .jprotect_hr_contract import *

import base64
from datetime import datetime
from io import BytesIO

import openpyxl
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from ...tristar_common.utils import utils


class TristarExportWorkday(models.TransientModel):
    _name = 'tristar.export.workday'
    _description = 'Tristar Export Workday'

    department_id = fields.Many2one('hr.department')
    month = fields.Selection([
        ('1', '01'),
        ('2', '02'),
        ('3', '03'),
        ('4', '04'),
        ('5', '05'),
        ('6', '06'),
        ('7', '07'),
        ('8', '08'),
        ('9', '09'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ], string='Tháng', default=lambda self: str(fields.Date.today().month))
    year = fields.Char('Năm', default=lambda self: str(fields.Date.today().year))
    lunch_boarding_house_file = fields.Binary('Dữ liệu tiền ăn, nhà trọ')

    @api.model
    # def get_workday_type_name_ot_holiday(self, is_not_need_confirm, activity, actual_start_time, actual_end_time):
    def get_workday_type_name_ot_holiday(self, line):
        return jprotect_cm_TristarExportWorkday_get_workday_type_name_ot_holiday(self, line, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_workday_type_holiday(self, other_activity_ids, line, is_not_need_confirm, code):
        return jprotect_cm_TristarExportWorkday_get_workday_type_holiday(self, other_activity_ids, line, is_not_need_confirm, code, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_workday_type_name_leave(self, activity, actual_start_time, actual_end_time):
        return jprotect_cm_TristarExportWorkday_get_workday_type_name_leave(self, activity, actual_start_time, actual_end_time, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_ot_time(self, start_ot_time, actual_end_time, is_leave_day=True):
        return jprotect_cm_TristarExportWorkday_get_ot_time(self, start_ot_time, actual_end_time, is_leave_day=True, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_workday_type_name_ot(self, line, holiday=False):
        return jprotect_cm_TristarExportWorkday_get_workday_type_name_ot(self, line, holiday=False, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_work_night_time(self, actual_end_time, start_ot_time):
        return jprotect_cm_TristarExportWorkday_get_work_night_time(self, actual_end_time, start_ot_time, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_workday_type_name_night(self, is_not_need_confirm, activity, actual_start_time, actual_end_time):
        return jprotect_cm_TristarExportWorkday_get_workday_type_name_night(self, is_not_need_confirm, activity, actual_start_time, actual_end_time, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_late_time(self, workday_schedule, employee):
        return jprotect_cm_TristarExportWorkday_get_late_time(self, workday_schedule, employee, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_gasoline_fee(self, workday_schedule, employee):
        return jprotect_cm_TristarExportWorkday_get_gasoline_fee(self, workday_schedule, employee, TristarExportWorkday=TristarExportWorkday, )

    def get_leave_sign(self, leave_activities, actual_start_time, actual_end_time):
        return jprotect_cm_TristarExportWorkday_get_leave_sign(self, leave_activities, actual_start_time, actual_end_time, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_hr_workday_type(self, line, employee):
        return jprotect_cm_TristarExportWorkday_get_hr_workday_type(self, line, employee, TristarExportWorkday=TristarExportWorkday, )

    @api.multi
    def get_lunch_boarding_house_fee_data(self):
        return jprotect_cm_TristarExportWorkday_get_lunch_boarding_house_fee_data(self, TristarExportWorkday=TristarExportWorkday, )

    @api.multi
    def apply_export(self):
        return jprotect_cm_TristarExportWorkday_apply_export(self, TristarExportWorkday=TristarExportWorkday, )

    @api.multi
    def apply_export_kitchen(self):
        return jprotect_cm_TristarExportWorkday_apply_export_kitchen(self, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_hr_workday_type_kitchen(self, line, employee):
        return jprotect_cm_TristarExportWorkday_get_hr_workday_type_kitchen(self, line, employee, TristarExportWorkday=TristarExportWorkday, )

    @api.model
    def get_workday_type_name_ot_kitchen(self, is_work_two_shift, break_time, plan_start_time, plan_end_time, actual_start_datetime, actual_end_datetime, ot_from, ot_to):
        return jprotect_cm_TristarExportWorkday_get_workday_type_name_ot_kitchen(self, is_work_two_shift, break_time, plan_start_time, plan_end_time, actual_start_datetime, actual_end_datetime, ot_from, ot_to, TristarExportWorkday=TristarExportWorkday, )
    # region: hieudt
    def x_ot_amount(self, x, y, standard=(8, 17), night_standard=(22, 30)):
        return jprotect_cm_TristarExportWorkday_x_ot_amount(self, x, y, standard=(8, 17), night_standard=(22, 30), TristarExportWorkday=TristarExportWorkday, )

if __name__ == '__main__':
    print(TristarExportWorkday.x_ot_amount(None, 8, 25, standard=None))
