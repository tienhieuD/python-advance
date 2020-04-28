import base64
from datetime import datetime
from io import BytesIO

import openpyxl
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from ...tristar_common.utils import utils


def jprotect_cm_TristarExportWorkday_get_workday_type_name_ot_holiday(self, line, TristarExportWorkday=None, ):
    return self.get_workday_type_name_ot(line, holiday=True)


def jprotect_cm_TristarExportWorkday_get_workday_type_holiday(self, other_activity_ids, line, is_not_need_confirm, code, TristarExportWorkday=None, ):
    if not line.state == 'head_of_department_confirm' and not is_not_need_confirm:
        return code


    hr_workday_type_activity = self.get_workday_type_name_ot_holiday(line)
    hr_workday_type = '%s%s' % (code, hr_workday_type_activity)
    return hr_workday_type


def jprotect_cm_TristarExportWorkday_get_workday_type_name_leave(self, activity, actual_start_time, actual_end_time, TristarExportWorkday=None, ):
    leave_paid_id = self.env.ref('tristar_leave.leave_paid')
    if activity.hr_leave_type_id == leave_paid_id:
        return 'R'
    if activity.hr_leave_time == 'all_day':
        hr_workday_type_name = 'P'
    else:
        if actual_start_time and actual_end_time:
            hr_workday_type_name = '0.5P0.5X'
        elif not actual_start_time and not actual_end_time:
            hr_workday_type_name = '0.5P0.5N'
        else:
            hr_workday_type_name = '!0.5P'
    return hr_workday_type_name

def jprotect_cm_TristarExportWorkday_get_ot_time(self, start_ot_time, actual_end_time, is_leave_day=True, TristarExportWorkday=None, ):
    ot_timeline = datetime.strptime("22:00", "%H:%M")

    start_new_day = datetime.strptime("08:00", "%H:%M") + relativedelta(days=1)
    actual_end_time = min(start_new_day, actual_end_time)

    if actual_end_time > ot_timeline:
        if start_ot_time <= ot_timeline:
            actual_ot_day_time = relativedelta(ot_timeline, start_ot_time)
            actual_ot_night_time = relativedelta(actual_end_time, ot_timeline)
            ot_day_time = utils.round_ot_time(actual_ot_day_time.hours, actual_ot_day_time.minutes)
            ot_night_time = utils.round_ot_time(actual_ot_night_time.hours, actual_ot_night_time.minutes)
            hr_workday_type_name = '%sđ%s' % (ot_day_time, ot_night_time)
        else:
            actual_ot_night_time = relativedelta(actual_end_time, start_ot_time)
            ot_night_time = utils.round_ot_time(actual_ot_night_time.hours, actual_ot_night_time.minutes)
            hr_workday_type_name = '0đ%s' % (ot_night_time)
    else:
        actual_ot_time = relativedelta(actual_end_time, start_ot_time)
        ot_time = utils.round_ot_time(actual_ot_time.hours, actual_ot_time.minutes)
        hr_workday_type_name = '%s' % ot_time
    return hr_workday_type_name

def jprotect_cm_TristarExportWorkday_get_workday_type_name_ot(self, line, holiday=False, TristarExportWorkday=None, ):
    ot_activities = line.other_activity_ids.filtered(lambda a: a.type == 'ot')
    if ot_activities:
        ot_day_total = 0.0
        ot_night_total = 0.0
        for activity in ot_activities:

            activity_start = utils.time2float(activity.start_ot_time)
            activity_end = utils.time2float(activity.end_ot_time)
            activity_end += 24 if activity_end < activity_start else 0

            if activity_start < line.plan_start_time and activity_end < line.plan_start_time:
                activity_start += 24
                activity_end += 24

            real_start = utils.time2float(line.add_start_time or line.actual_start_time)
            real_end = utils.time2float(line.add_end_time or line.actual_end_time)
            real_end += 24 if real_end < real_start else 0

            x = max(activity_start, real_start)
            y = min(activity_end, real_end)

            standard = None if holiday else (8, 17)
            amount_day, amount_night = self.x_ot_amount(x, y, standard=standard)

            ot_day_total += amount_day
            ot_night_total += amount_night

        ot_day_total = ot_day_total - (ot_day_total % 0.25)
        ot_night_total = ot_night_total - (ot_night_total % 0.25)

        if ot_night_total:
            return '%sđ%s' % (ot_day_total or '0', ot_night_total)
        elif ot_day_total:
            return '%s' % ot_day_total
    return ''

def jprotect_cm_TristarExportWorkday_get_work_night_time(self, actual_end_time, start_ot_time, TristarExportWorkday=None, ):
    actual_ot_night_time = relativedelta(actual_end_time, start_ot_time)
    ot_night_time = utils.round_ot_time(actual_ot_night_time.hours, actual_ot_night_time.minutes)
    if ot_night_time > 0:
        hr_workday_type_name = '0đ%s' % ot_night_time
    else:
        hr_workday_type_name = ''
    return hr_workday_type_name

def jprotect_cm_TristarExportWorkday_get_workday_type_name_night(self, is_not_need_confirm, activity, actual_start_time, actual_end_time, TristarExportWorkday=None, ):
    hr_workday_type_name = ''
    if not (actual_start_time and actual_end_time):
        return hr_workday_type_name

    start_ot_time = datetime.strptime(activity.start_ot_time, "%H:%M")
    end_ot_time = datetime.strptime(activity.end_ot_time, "%H:%M")
    if end_ot_time < start_ot_time:
        end_ot_time += relativedelta(days=1)

    if is_not_need_confirm:
        hr_workday_type_name = self.get_ot_time(start_ot_time, end_ot_time)
        return hr_workday_type_name

    actual_start_time = datetime.strptime(actual_start_time, "%H:%M")
    actual_end_time = datetime.strptime(actual_end_time, "%H:%M")
    if actual_start_time > actual_end_time:
        actual_end_time += relativedelta(days=1)

    if actual_end_time <= start_ot_time:
        hr_workday_type_name = ''
    else:
        if actual_end_time > end_ot_time:
            actual_end_time = end_ot_time
        hr_workday_type_name = self.get_work_night_time(actual_end_time, start_ot_time)
    return hr_workday_type_name

def jprotect_cm_TristarExportWorkday_get_late_time(self, workday_schedule, employee, TristarExportWorkday=None, ):
    workday_schedule_line_ids = workday_schedule.workday_schedule_line_ids
    late_time_minutes = 0  # minutes
    for line in workday_schedule_line_ids:
        actual_start_time = line.add_start_time or line.actual_start_time
        is_not_need_confirm = employee.is_not_need_confirm  # Trường hợp giám đốc, quản lý không cần xác nhận
        if not actual_start_time or is_not_need_confirm:
            continue
        other_activity_ids = line.other_activity_ids
        working_hours = employee.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == line.day_of_week)
        if not working_hours:
            continue
        start_morning_time = working_hours.filtered(lambda r: r.day_period == 'morning')[:1].hour_from or 8.0
        end_morning_time = working_hours.filtered(lambda r: r.day_period == 'morning')[:1].hour_to or 12.0
        start_afternoon_time = working_hours.filtered(lambda r: r.day_period == 'afternoon')[:1].hour_from or 13.5  # Trường hợp thứ 7, chủ nhật không có trong working_hours, tạm thời fix sẽ confirm lại

        if (other_activity_ids and other_activity_ids.filtered(lambda r: r.hr_leave_time == 'morning') and line.state == 'head_of_department_confirm') or datetime.strptime(actual_start_time, "%H:%M") > datetime.strptime(utils.float_to_time(end_morning_time - 0.25), "%H:%M"):
            late_time_obj = relativedelta(datetime.strptime(actual_start_time, "%H:%M"),
                                          datetime.strptime(utils.float_to_time(start_afternoon_time), "%H:%M"))
        else:
            late_time_obj = relativedelta(datetime.strptime(actual_start_time, "%H:%M"),
                                          datetime.strptime(utils.float_to_time(start_morning_time), "%H:%M"))
        if late_time_obj:
            late_time_minutes += max(late_time_obj.hours * 60 + late_time_obj.minutes, 0)

    return late_time_minutes

def jprotect_cm_TristarExportWorkday_get_gasoline_fee(self, workday_schedule, employee, TristarExportWorkday=None, ):
    workday_schedule_line_ids = workday_schedule.workday_schedule_line_ids
    gasoline_fee = 0
    for line in workday_schedule_line_ids:
        other_activity_ids = line.other_activity_ids
        is_not_need_confirm = employee.is_not_need_confirm
        if other_activity_ids and (line.state == 'head_of_department_confirm' or is_not_need_confirm):
            for activity in other_activity_ids:

                if activity.type != 'kitchen':
                    continue
                if activity.kitchen_type == 'company_car':
                    continue
                kitchen_unit_price = activity.work_kitchen_place.kitchen_unit_price or 0
                const = 1 if activity.gasoline_costs == 'one_way' else 2
                gasoline_fee += kitchen_unit_price * const
    return gasoline_fee

def jprotect_cm_TristarExportWorkday_get_leave_sign(self, leave_activities, actual_start_time, actual_end_time, TristarExportWorkday=None, ):
    WRONG_VALS = {
        '0.5P0.5P': 'P',
        '0.5R0.5R': 'R',
        '0.5NB0.5NB': 'NB',
    }
    LEAVE_TYPE_MARK = {
        self.env.ref('tristar_leave.leave_baby').id: 'R',
        self.env.ref('tristar_leave.leave_marriage').id: 'R',
        self.env.ref('tristar_leave.leave_child_marriage').id: 'R',
        self.env.ref('tristar_leave.leave_wife').id: 'R',
        self.env.ref('tristar_leave.leave_death').id: 'R',
        self.env.ref('tristar_leave.leave_paid').id: 'R',
        self.env.ref('tristar_leave.leave_holiday').id: 'R',
        self.env.ref('tristar_leave.leave_free').id: 'N',
        self.env.ref('tristar_leave.leave_night').id: 'NB',
        self.env.ref('tristar_leave.leave_weekend').id: 'NB',
    }
    sign = ''
    total_amount = 0  # Tổng số phép xin nghỉ trong ngày

    for activity in leave_activities:
        mark = LEAVE_TYPE_MARK.get(activity.hr_leave_type_id.id, 'P')
        amount = 0.5 if activity.hr_leave_time in ('morning', 'afternoon') else 1
        sign += '%s%s' % ('' if amount == 1 else amount, mark)
        total_amount += amount

    if total_amount < 1:
        if actual_start_time and actual_end_time:
            sign = '0.5X' + sign
        else:
            sign = sign + '0.5N'

    if sign in WRONG_VALS:
        for wrong_val, right_val in WRONG_VALS.items():
            sign = sign.replace(wrong_val, right_val)

    return sign

def jprotect_cm_TristarExportWorkday_get_hr_workday_type(self, line, employee, TristarExportWorkday=None, ):
    actual_start_time = line.add_start_time or line.actual_start_time
    actual_end_time = line.add_end_time or line.actual_end_time
    other_activity_ids = line.other_activity_ids
    is_not_need_confirm = employee.is_not_need_confirm  # Trường hợp giám đốc, quản lý không cần xác nhận
    plan_start_time = line.plan_start_time
    plan_end_time = line.plan_end_time
    working_hours = employee.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == line.day_of_week)
    end_morning_time = working_hours.filtered(lambda r: r.day_period == 'morning')[:1].hour_to or 12.0
    start_afternoon_time = working_hours.filtered(lambda r: r.day_period == 'afternoon')[:1].hour_from or 13.5

    date = line.date
    if self.env['transfer.temp.order.line'].is_transfer_on_date(employee, date):
        return 'TC'

    working_hours = employee.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == str(date.weekday()))
    if self.env['public.holiday'].get_holiday(date, count=True):
        return self.get_workday_type_holiday(other_activity_ids, line, is_not_need_confirm, code='L')
    if not working_hours or (date.weekday() == 5 and self.env['saturday.working.plan'].search_count([('date_saturday', '=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)), ('is_working_day', '=', False)])):
        return self.get_workday_type_holiday(other_activity_ids, line, is_not_need_confirm, code='T')

    hr_workday_type_activity = ''
    if other_activity_ids and (line.state == 'head_of_department_confirm' or is_not_need_confirm):

        leave_activities = other_activity_ids.filtered(lambda ac: ac.type == 'leave')
        if leave_activities:
            hr_workday_type_activity += self.get_leave_sign(leave_activities, actual_start_time, actual_end_time)

        hr_workday_type_activity += self.get_workday_type_name_ot(line)

        for activity in other_activity_ids:
            activity_type = activity.type
            hr_workday_type_name = ''
            if activity_type == 'leave':
                continue

            elif activity_type == 'ot':
                continue

            elif activity_type == 'kitchen':
                hr_workday_type_name = ''
            else:
                hr_workday_type_name = self.get_workday_type_name_night(is_not_need_confirm, activity, actual_start_time, actual_end_time)

            hr_workday_type_activity += hr_workday_type_name

    if is_not_need_confirm:  # Trường hợp giám đốc,... mặc định giờ vào ra theo kế hoạch
        actual_start_time = utils.float_to_time(plan_start_time)
        actual_end_time = utils.float_to_time(plan_end_time)

    if not (other_activity_ids.filtered(lambda r: r.type == 'leave') and line.state == 'head_of_department_confirm'):
        if actual_start_time and actual_end_time:
            actual_start_datetime = datetime.strptime(actual_start_time, "%H:%M")
            end_morning_datetime = datetime.strptime(utils.float_to_time(end_morning_time), "%H:%M")
            actual_end_datetime = datetime.strptime(actual_end_time, "%H:%M")
            start_afternoon_datetime = datetime.strptime(utils.float_to_time(start_afternoon_time), "%H:%M")
            if actual_start_datetime > actual_end_datetime:
                actual_end_datetime += relativedelta(days=1)
            if actual_start_datetime > end_morning_datetime - relativedelta(minutes=15) or actual_end_datetime < start_afternoon_datetime - relativedelta(minutes=15):
                hr_workday_type = '0.5X0.5N%s' % hr_workday_type_activity
            else:
                hr_workday_type = 'X%s' % hr_workday_type_activity
            if not is_not_need_confirm and not (line.actual_start_time and line.actual_end_time):
                return '!%s' % hr_workday_type
        elif not actual_start_time and not actual_end_time:
            hr_workday_type = 'N'
        else:
            hr_workday_type = '!X'
    else:
        hr_workday_type = hr_workday_type_activity

    return hr_workday_type

def jprotect_cm_TristarExportWorkday_get_lunch_boarding_house_fee_data(self, TristarExportWorkday=None, ):
    file = self.lunch_boarding_house_file
    if not file:
        return {}
    workbook = openpyxl.load_workbook(filename=BytesIO(base64.decodebytes(file)))
    main_sheet = workbook.active
    res = {}
    for row in [v for v in main_sheet.values]:
        if row[0] == 'sequence':
            continue
        employees = self.env['hr.employee'].name_search(row[2])
        employee_id = employees[0][0] if employees else 0
        lunch_fee, boarding_house_fee = row[3], row[4]
        res[employee_id] = {
            'lunch_fee': lunch_fee,
            'boarding_house_fee': boarding_house_fee,
        }
    return res

def jprotect_cm_TristarExportWorkday_apply_export(self, TristarExportWorkday=None, ):
    self.ensure_one()
    if not self.month or not self.year:
        raise ValidationError('Vui lòng nhập đầy đủ thông tin!')

    lunch_boarding_house_fee_data = self.get_lunch_boarding_house_fee_data()  # hieudt
    month = self.month
    year = self.year

    department_office_parent = self.env.ref('tristar_common.department_office')
    employee_ids = self.env['hr.employee'].sudo().search([('department_id', 'child_of', department_office_parent.ids)])
    workday_schedule_not_confirm = self.env['workday.schedule']
    for employee in employee_ids:
        workday_schedule = self.env['workday.schedule'].sudo().search([('employee_id', '=', employee.id), ('month', '=', month), ('year', '=', year)], limit=1)
        if not workday_schedule:
            continue
        if workday_schedule.status == 'draft':
            workday_schedule_not_confirm |= workday_schedule
            continue
        values = {
            'employee_id': employee.id,
            'workday_month': int(month),
            'workday_year': int(year),
        }
        workday_schedule_line_ids = workday_schedule.workday_schedule_line_ids

        for line in workday_schedule_line_ids:
            day = line.date.day
            hr_workday_type = self.get_hr_workday_type(line, employee)
            hr_workday_type_id = self.env['hr.workday.type'].sudo().search([('name', '=', hr_workday_type)], limit=1)
            if not hr_workday_type_id:
                hr_workday_type_id = self.env['hr.workday.type'].sudo().create({'name': hr_workday_type})
            values['day_%s' % day] = hr_workday_type_id.id

        late_time_minutes = self.get_late_time(workday_schedule, employee)
        values['late_time_minutes'] = late_time_minutes
        gasoline_fee = self.get_gasoline_fee(workday_schedule, employee)
        values['gasoline_fee'] = gasoline_fee

        values['lunch_fee'] = lunch_boarding_house_fee_data.get(employee.id, {}).get('lunch_fee', 0)
        values['boarding_house_fee'] = lunch_boarding_house_fee_data.get(employee.id, {}).get('boarding_house_fee', 0)

        hr_workday_office_line_id = self.env['hr.workday.office.line'].sudo().search([('employee_id', '=', employee.id), ('workday_month', '=', int(month)), ('workday_year','=', int(year))], limit=1)
        if not hr_workday_office_line_id:
            hr_workday_office_line_id = self.env['hr.workday.office.line'].sudo().create(values)
        else:
            hr_workday_office_line_id.sudo().write(values)

    if workday_schedule_not_confirm:
        view = self.env.ref('tristar_payroll_office.popup_office_workday_not_confirm')
        employee = workday_schedule_not_confirm.mapped('employee_id.name')
        content = ''
        for emp in employee:
            content += '<li>%s</li>' % emp
        new_view = '''
        <form string="">
            <sheet>
                <h3>Nhân viên sau sẽ không tạo được bảng công</h3>
                <group>
                    {}
                </group>
            </sheet>
            <footer>
                <button name="view_workday" string="Xem bảng công" type="object" class="btn-primary"/>
                <button name="view_workday_schedule" string="Xem kế hoạch chưa xác nhận" type="object" class="btn-secondary"/>
            </footer>
        </form>
        '''.format(content)
        view.sudo().write({
            'arch_db': new_view,
        })
        context = {
            'employee_ids': workday_schedule_not_confirm.mapped('employee_id.id'),
            'month': month,
            'year': year,
        }
        return {
            'name': 'Kế hoạch làm việc chưa được xác nhận',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'popup.office.workday.not.confirm',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    return {'type': 'ir.actions.act_window',
            'name': 'Bảng lương',
            'res_model': 'hr.workday.office.line',
            'target': 'current',
            'view_mode': 'tree',
            'view_id': self.env.ref('tristar_payroll_office.hr_workday_office_line_tree').id,
            'domain': [('workday_month', '=', int(month)), ('workday_year', '=', int(year))],
            'context': {'screen': 'worked.day', 'screen_for': 'office', 'workday_year': year, 'workday_month': month}
            }

def jprotect_cm_TristarExportWorkday_apply_export_kitchen(self, TristarExportWorkday=None, ):
    self.ensure_one()
    if not self.month or not self.year or not self.department_id:
        raise ValidationError('Vui lòng nhập đầy đủ thông tin!')

    month = self.month
    year = self.year
    department = self.department_id
    employee_ids = self.env['hr.employee'].sudo().search([('department_id', '=', department.id)])
    workday_schedule_not_confirm = self.env['workday.schedule']
    for employee in employee_ids:
        workday_schedule = self.env['workday.schedule'].sudo().search([('employee_id', '=', employee.id), ('month', '=', month), ('year', '=', year)], limit=1)
        if not workday_schedule:
            continue
        if workday_schedule.status == 'draft':
            workday_schedule_not_confirm |= workday_schedule
            continue
        values = {
            'employee_id': employee.id,
            'workday_month': int(month),
            'workday_year': int(year),
        }
        workday_schedule_line_ids = workday_schedule.workday_schedule_line_ids
        values['belong_to_department_id'] = department.id

        for line in workday_schedule_line_ids:
            day = line.date.day
            hr_workday_type = self.get_hr_workday_type_kitchen(line, employee)
            hr_workday_type_id = self.env['hr.workday.type'].sudo().search([('name', '=', hr_workday_type)], limit=1)
            if not hr_workday_type_id:
                hr_workday_type_id = self.env['hr.workday.type'].sudo().create({'name': hr_workday_type})
            values['day_%s' % day] = hr_workday_type_id.id

        hr_workday_table_line_id = self.env['hr.workday.table.line'].sudo().search([('employee_id', '=', employee.id), ('workday_month', '=', int(month)), ('workday_year','=', int(year))])
        if not hr_workday_table_line_id:
            hr_workday_table_line_id = self.env['hr.workday.table.line'].sudo().create(values)
        else:
            hr_workday_table_line_id.sudo().write(values)

    if workday_schedule_not_confirm:
        view = self.env.ref('tristar_payroll_office.popup_canteen_workday_not_confirm')
        employee = workday_schedule_not_confirm.mapped('employee_id.name')
        content = ''
        for emp in employee:
            content += '<li>%s</li>' % emp
        new_view = '''
        <form string="">
            <sheet>
                <h3>Nhân viên sau sẽ không tạo được bảng công</h3>
                <group>
                    {}
                </group>
            </sheet>
            <footer>
                <button name="view_workday" string="Xem bảng công" type="object" class="btn-primary"/>
                <button name="view_workday_schedule" string="Xem kế hoạch chưa xác nhận" type="object" class="btn-secondary"/>
            </footer>
        </form>
        '''.format(content)
        view.sudo().write({
            'arch_db': new_view,
        })
        context = {
            'employee_ids': workday_schedule_not_confirm.mapped('employee_id.id'),
            'month': month,
            'year': year,
        }
        return {
            'name': 'Kế hoạch làm việc chưa được xác nhận',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'popup.canteen.workday.not.confirm',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    self.env['hr.workday.table.line'].recompute_workday(department, year, month)
    return {
        'type': 'ir.actions.act_window',
        'name': 'Bảng lương',
        'res_model': 'hr.workday.table.line',
        'target': 'current',
        'view_mode': 'tree',
        'view_id': self.env.ref('tristar_payroll_canteen.hr_workday_line_tree').id,
        'domain': [
            ('workday_month', '=', int(month)),
            ('workday_year', '=', int(year)),
            ('belong_to_department_id', '=', department.id),
        ],
        'context': {
            'screen': 'worked.day',
            'screen_for': 'canteen',
            'department_id': department.id,
            'workday_year': year,
            'workday_month': month
        }
    }

def jprotect_cm_TristarExportWorkday_get_hr_workday_type_kitchen(self, line, employee, TristarExportWorkday=None, ):
    actual_start_time = line.add_start_time or line.actual_start_time
    actual_end_time = line.add_end_time or line.actual_end_time
    other_activity_ids = line.other_activity_ids
    is_not_need_confirm = employee.is_not_need_confirm  # Trường hợp giám đốc, quản lý không cần xác nhận
    plan_start_time = line.plan_start_time
    plan_end_time = line.plan_end_time

    date = line.date
    if self.env['transfer.temp.order.line'].is_transfer_on_date(employee, date):
        return 'TC'

    working_hours = employee.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == str(date.weekday()))
    if self.env['public.holiday.canteen'].get_holiday(date, count=True, department=employee.department_id):
        return self.get_workday_type_holiday(other_activity_ids, line, is_not_need_confirm, code='LL')
    if not working_hours:
        return self.get_workday_type_holiday(other_activity_ids, line, is_not_need_confirm, code='T')

    hr_workday_type_activity = ''
    if other_activity_ids and (line.state == 'head_of_department_confirm' or is_not_need_confirm):
        for activity in other_activity_ids:
            activity_type = activity.type
            hr_workday_type_name = ''
            if activity_type == 'leave':
                hr_workday_type_name = self.get_workday_type_name_leave(activity, actual_start_time, actual_end_time)

            hr_workday_type_activity += hr_workday_type_name

    if is_not_need_confirm:  # Trường hợp giám đốc,... mặc định giờ vào ra theo kế hoạch
        actual_start_time = utils.float_to_time(plan_start_time)
        actual_end_time = utils.float_to_time(plan_end_time)

    if not (other_activity_ids.filtered(lambda r: r.type == 'leave') and line.state == 'head_of_department_confirm'):
        if actual_start_time and actual_end_time:
            actual_start_datetime = datetime.strptime(actual_start_time, "%H:%M")
            actual_end_datetime = datetime.strptime(actual_end_time, "%H:%M")
            if actual_start_datetime > actual_end_datetime:
                actual_end_datetime += relativedelta(days=1)
            ot_from = datetime.strptime(utils.float_to_time(line.ot_from), "%H:%M")
            ot_to = datetime.strptime(utils.float_to_time(line.ot_to), "%H:%M")
            break_time = employee.resource_calendar_id.break_time
            is_work_two_shift = line.is_work_two_shift
            if ot_from > ot_to:
                ot_to += relativedelta(days=1)

            if actual_end_datetime < ot_from:
                hr_workday_type = 'X'
            else:
                hr_workday_type = self.get_workday_type_name_ot_kitchen(is_work_two_shift, break_time, plan_start_time, plan_end_time, actual_start_datetime, actual_end_datetime, ot_from, ot_to)

            if not line.actual_start_time or not line.actual_end_time:
                return '!%s' % hr_workday_type
        elif not actual_start_time and not actual_end_time:
            hr_workday_type = 'N'
        else:
            hr_workday_type = '!X'
    else:
        hr_workday_type = hr_workday_type_activity

    return hr_workday_type

def jprotect_cm_TristarExportWorkday_get_workday_type_name_ot_kitchen(self, is_work_two_shift, break_time, plan_start_time, plan_end_time, actual_start_datetime, actual_end_datetime, ot_from, ot_to, TristarExportWorkday=None, ):
    if ot_to == ot_from:
        return 'X'

    plan_start_datetime = datetime.strptime(utils.float_to_time(plan_start_time), "%H:%M")
    plan_end_datetime = datetime.strptime(utils.float_to_time(plan_end_time), "%H:%M")
    if plan_start_datetime > plan_end_datetime:
        plan_end_datetime += relativedelta(days=1)
    hours_per_shift_obj = relativedelta(plan_end_datetime, plan_start_datetime)
    hours_per_shift = utils.round_ot_time_kitchen(hours_per_shift_obj.hours, hours_per_shift_obj.minutes)

    ot_time_obj = relativedelta(actual_end_datetime, ot_from)
    ot_time = utils.round_ot_time_kitchen(ot_time_obj.hours, ot_time_obj.minutes)


    total_work_time_obj = relativedelta(actual_end_datetime, actual_start_datetime)
    total_work_time = utils.round_ot_time_kitchen(total_work_time_obj.hours, total_work_time_obj.minutes)

    if actual_start_datetime >= plan_end_datetime or actual_end_datetime <= plan_start_datetime:
        return 'N'

    ot_time_if_work_two_shift = total_work_time - (2 * break_time) - (hours_per_shift * 2)
    if is_work_two_shift and ot_time_if_work_two_shift > 0:
        workday_type_name = 'XĐ%s' % ot_time_if_work_two_shift
    else:
        workday_type_name = 'X%s' % (ot_time or '')

    return workday_type_name

def jprotect_cm_TristarExportWorkday_x_ot_amount(self, x, y, standard=(8, 17), night_standard=(22, 30), TristarExportWorkday=None, ):
    """
    :param x: giờ tính ot bđ
    :param y: giờ tính ot kt
    :param standard: khoảng giờ làm chuẩn không OT
    :param night_standard: khoảng giờ làm tính OT đêm
    :return:
    """
    n8 = standard and standard[0] or 8
    n17 = standard and standard[1] or 8
    n22 = night_standard and night_standard[0] or 22
    n30 = night_standard and night_standard[1] or 22
    amount_day = max(0, min(n8, y) - max(x, n30 - 24)) + max(0, min(n22, y) - max(n17, x)) + max(0, min(n8 + 24, y) - n30)
    amount_night = max(0, n30 - 24 - x) + max(0, min(n30, y) - max(n22, x))
    return amount_day, amount_night


