from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OfficeVisitor(models.Model):
    _name = 'office.visitor'
    _description = 'Office Visitor'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Visitor Name', required=True, tracking=True)
    place = fields.Char(string='Place', required=True)
    reason = fields.Text(string='Reason for Visit', required=True)
    host_employee_id = fields.Many2one(
        'hr.employee', string='Employee to Meet', required=True, tracking=True)
    badge_number = fields.Char(
        string='Badge Number', readonly=True, copy=False, default='New')
    visit_date = fields.Date(
        string='Visit Date', default=fields.Date.context_today)
    check_in_time = fields.Datetime(
        string='Check-in Time', readonly=True, copy=False)
    check_out_time = fields.Datetime(
        string='Check-out Time', readonly=True, copy=False)
    state = fields.Selection(
        [('registered', 'Registered'),
         ('checked_in', 'Checked In'),
         ('checked_out', 'Checked Out')],
        string='Status', default='registered', tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        # Generate the badge number automatically (VIS/0001, VIS/0002, ...)
        for vals in vals_list:
            if vals.get('badge_number', 'New') == 'New':
                vals['badge_number'] = (
                    self.env['ir.sequence'].next_by_code('office.visitor') or 'New')
        return super().create(vals_list)

    def action_check_in(self):
        for rec in self:
            if rec.state != 'registered':
                raise UserError(_("Only registered visitors can be checked in."))
            rec.write({
                'check_in_time': fields.Datetime.now(),
                'state': 'checked_in',
            })
            rec._notify_employee()

    def action_check_out(self):
        for rec in self:
            if rec.state != 'checked_in':
                raise UserError(_("Only checked-in visitors can be checked out."))
            rec.write({
                'check_out_time': fields.Datetime.now(),
                'state': 'checked_out',
            })

    def action_print_badge(self):
        self.ensure_one()
        return self.env.ref(
            'office_visitor.action_report_visitor_badge').report_action(self)

    def _notify_employee(self):
        self.ensure_one()
        employee = self.host_employee_id
        # 1) Email to the employee (template is added later in the module)
        template = self.env.ref(
            'office_visitor.email_template_visitor_arrival',
            raise_if_not_found=False)
        if template and employee.work_email:
            template.send_mail(self.id, force_send=False)
        # 2) Pop-up notification inside Odoo, if the employee has a user
        partner = employee.user_id.partner_id
        if partner:
            self.env['bus.bus']._sendone(partner, 'simple_notification', {
                'title': _("Visitor Arrived"),
                'message': _("%(visitor)s is here to meet you.", visitor=self.name),
                'type': 'info',
                'sticky': True,
            })
