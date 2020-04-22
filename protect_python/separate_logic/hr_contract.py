from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

FAIL_CONTRACT_MSG = _("Contract is not confirmed")
def __protect__set_to_lvl1_confirm(self):
    return self.write({
        'state': 'draft',
        'status': 'management_level_1_confirm',
    })

def __protect__create(self, vals, Contract):
    employee_id = vals.get('employee_id')
    if employee_id:
        employee_contract = self.sudo().search([('employee_id', '=', employee_id)])
        if employee_contract:
            raise ValidationError('Nhân viên không thể có 2 hợp đồng')
    res = super(Contract, self).create(vals)
    if not res.is_valid_contract():
        raise ValidationError(FAIL_CONTRACT_MSG)
    return res

class Contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    wage = fields.Float(digits=(16, 0), track_visibility='onchange')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('management_level_1_confirm', 'Management level 1 confirm'),
        ('management_level_2_confirm', 'Management level 2 confirm'),
    ], 'Confirm Status', default='draft', track_visibility='always')

    # name = fields.Char(track_visibility='onchange')
    # department_id = fields.Many2one(track_visibility='onchange')
    # job_id = fields.Many2one(track_visibility='onchange')
    # date_start = fields.Date(track_visibility='onchange')
    # date_end = fields.Date(track_visibility='onchange')
    # trial_date_end = fields.Date(track_visibility='onchange')
    # advantages = fields.Text(track_visibility='onchange')
    # notes = fields.Text(track_visibility='onchange')
    # state = fields.Selection(track_visibility='onchange')
    # schedule_pay = fields.Selection(track_visibility='onchange')

    @api.model
    def create(self, vals):
        return __protect__create(self, vals, Contract)

    @api.multi
    def set_to_lvl1_confirm(self):
        return __protect__set_to_lvl1_confirm(self)

    @api.multi
    def management_level_1_confirm(self):
        for rec in self:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'user_id': rec.department_id.person_manager_contract_ids.ids and rec.department_id.person_manager_contract_ids.ids[0] or 2,
                'summary': "Hợp đồng vừa được xác nhận lần 1",
                'automated': True,
                'date_deadline': fields.Date.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': rec.id,
            })
        return self.write({'status': 'management_level_1_confirm',})

    @api.multi
    def management_level_2_confirm(self):
        for rec in self:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'user_id': rec.department_id.person_manager_contract_ids.ids and rec.department_id.person_manager_contract_ids.ids[0] or 2,
                'summary': "Hợp đồng vừa được xác nhận lần 2",
                'automated': True,
                'date_deadline': fields.Date.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': rec.id,
            })
        return self.write({
            'state': 'open',
            'status': 'management_level_2_confirm',
        })

    @api.multi
    def is_valid_contract(self):
        return not any(contract.state in ['open'] and contract.status != 'management_level_2_confirm'
                       for contract in self)

    @api.multi
    def write(self, vals):
        employee_id = vals.get('employee_id')
        if employee_id:
            employee_contract = self.sudo().search([('employee_id', '=', employee_id)])
            if employee_contract:
                raise ValidationError('Nhân viên không thể có 2 hợp đồng')
        res = super(Contract, self).write(vals)
        if not self.is_valid_contract():
            raise ValidationError(FAIL_CONTRACT_MSG)

        if self._context.get('is_cron_salary_adjustment'):
            return res

        is_user_lvl_1 = self.env.user.has_group('tristar_common.group_hr_contract_manager_level_1')
        is_user_lvl_2 = self.env.user.has_group('tristar_common.group_hr_contract_manager_level_2')
        for rec in self:
            if rec.status == 'management_level_2_confirm' and not is_user_lvl_2:
                raise ValidationError(_('Chỉ người xác nhận cấp 2 mới có quyền sửa hợp đồng này'))
            if rec.status == 'management_level_1_confirm' and not (is_user_lvl_1 or is_user_lvl_2):
                raise ValidationError(_('Chỉ người xác nhận cấp 1 trở lên mới có quyền sửa hợp đồng này'))
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'status' in init_values and self.status == 'management_level_1_confirm':
            return 'tristar_common.mt_contract_validate1'
        elif 'status' in init_values and self.status == 'management_level_2_confirm':
            return 'tristar_common.mt_contract_validate2'
        return super(Contract, self)._track_subtype(init_values)


