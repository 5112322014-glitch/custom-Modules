from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class HrDocumentRequest(models.Model):
    _name = 'hr.document.request'
    _description = 'HR Document Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True
    )
    document_type = fields.Selection([
        ('salary_certificate', 'Salary Certificate'),
        ('experience_letter', 'Experience Letter'),
        ('noc', 'NOC'),
        ('other', 'Other')
    ], string='Document Type', required=True, tracking=True)

    reason = fields.Text(string='Purpose', required=True)
    required_by_date = fields.Date(string='Required By Date', required=True, tracking=True)
    requested_on = fields.Date(string='Requested On', default=fields.Date.context_today, readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)

    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_on = fields.Date(string='Approved On', readonly=True, copy=False)
    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)

    document_attachment = fields.Binary(string='Attached Letter/Document', attachment=True)
    attachment_filename = fields.Char(string='Filename')

    # Letter ke liye joining date, designation aur company name.
    # sudo() isliye ke normal employee hr.employee ke private fields read
    # nahi kar sakta, lekin apne letter mein yeh chahiye.
    joining_date = fields.Date(
        string='Joining Date',
        compute='_compute_employee_details',
    )
    designation = fields.Char(
        string='Designation',
        compute='_compute_employee_details',
    )
    company_id_name = fields.Char(
        string='Company Name',
        compute='_compute_employee_details',
    )

    @api.depends('employee_id')
    def _compute_employee_details(self):
        for record in self:
            emp = record.employee_id.sudo()
            record.joining_date = emp.joining_date
            record.designation = emp.job_id.name or emp.job_title or ''
            record.company_id_name = emp.company_id.name or ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.document.request') or _('New')
        return super(HrDocumentRequest, self).create(vals_list)

    def _check_hr_manager(self):
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(_("Only HR Managers are allowed to perform this action!"))

    @api.constrains('required_by_date')
    def _check_required_by_date(self):
        # CHANGE (Timezone): pehle date.today() tha, jo server ki (UTC) date deta hai.
        # Kyun: raat ko user aur server ki "aaj" ki date alag hoti hai, to
        # constraint kabhi galat accept karta tha, kabhi galat reject.
        # Ab context_today user ke timezone ke hisab se aaj ki date deta hai.
        today = fields.Date.context_today(self)
        for record in self:
            if record.required_by_date and record.required_by_date < today:
                raise ValidationError(_("The required-by date cannot be in the past."))

    @api.constrains('state', 'employee_id')
    def _check_max_submitted_requests(self):
        for record in self:
            if record.state == 'submitted':
                submitted_count = self.search_count([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'submitted'),
                    ('id', '!=', record.id)
                ])
                if submitted_count >= 3:
                    raise ValidationError(_("An employee cannot have more than 3 submitted requests at the same time."))

    @api.constrains('state', 'rejection_reason')
    def _check_rejection_reason(self):
        for record in self:
            if record.state == 'rejected' and not record.rejection_reason:
                raise ValidationError(_("A rejection reason is mandatory when rejecting a request."))

    # CHANGE (Issued lock): pehle issued hote hi har field block thi.
    # Ab sirf business fields lock hain, chatter/technical fields chal sakti hain.
    # Kyun: official record ko chupke se badalne se rokna hai, lekin system ke
    # apne likhne (chatter, activity) ko nahi rokna.
    LOCKED_FIELDS = {
        'employee_id', 'document_type', 'reason', 'required_by_date',
        'document_attachment', 'attachment_filename', 'state',
        'approved_by_id', 'approved_on', 'rejection_reason',
    }

    def write(self, vals):
        touched = self.LOCKED_FIELDS & set(vals)
        if touched and not self.env.context.get('allow_issued_edit'):
            for record in self:
                if record.state == 'issued':
                    raise UserError(_(
                        "This request is issued and locked. "
                        "Ask an HR Manager to reopen it to correct: %s",
                        ', '.join(sorted(touched))
                    ))
        return super(HrDocumentRequest, self).write(vals)

    def action_submit(self):
        for record in self:
            if not record.reason:
                raise UserError(_("The purpose/reason cannot be empty."))
            record.state = 'submitted'

    def action_approve(self):
        self._check_hr_manager()
        # CHANGE (Timezone): approved_on mein pehle fields.Date.today() tha (server date).
        # Kyun: wohi masla, approve karne wale ki local date ke bajaye UTC date save hoti thi.
        # Ab approve karne wale user ke timezone ki date save hoti hai.
        today = fields.Date.context_today(self)
        for record in self:
            record.write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_on': today,
            })

            record.message_post(
                body=_("Your HR document request has been approved."),
                partner_ids=[record.employee_id.user_id.partner_id.id] if record.employee_id.user_id else []
            )

    def action_reject(self):
        self._check_hr_manager()
        for record in self:
            if not record.rejection_reason:
                raise UserError(_("Please provide a rejection reason before rejecting."))
            record.state = 'rejected'

    def action_issue(self):
        self._check_hr_manager()
        for record in self:
            if not record.document_attachment:
                raise UserError(_("Please upload the attachment before issuing the document."))
            record.state = 'issued'

    def action_reset_to_draft(self):
        for record in self:
            if record.state != 'rejected':
                raise UserError(_("Only rejected requests can be reset to draft."))
            record.state = 'draft'
            
            
            
                # CHANGE (Issued lock): HR Manager ke liye controlled exception.
    # Kyun: typo ya galat attachment theek karne ka raasta chahiye, lekin logged,
    # taake audit trail rahe.
    def action_reopen(self):
        self._check_hr_manager()
        for record in self:
            if record.state != 'issued':
                raise UserError(_("Only issued requests can be reopened."))
            record.with_context(allow_issued_edit=True).write({'state': 'approved'})
            record.message_post(body=_(
                "Request reopened by %s for correction.", self.env.user.name
            ))
