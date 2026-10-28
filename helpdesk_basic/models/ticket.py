from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    # Technical name (the database table will be helpdesk_basic_ticket)
    _name = 'helpdesk.basic.ticket'
    _description = 'Help Desk Ticket'
    # Adds the chatter (messages, notes and change history)
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # Most urgent first, then newest first
    _order = 'priority desc, id desc'

    # Ticket number, filled automatically in a later step
    name = fields.Char(string='Ticket Number', readonly=True, copy=False, default='New')
    subject = fields.Char(string='Subject', required=True, tracking=True)
    description = fields.Text(string='Description')

    # The user who created the ticket (current user by default)
    requester_id = fields.Many2one(
        'res.users', string='Raised By',
        default=lambda self: self.env.user, tracking=True,
    )
    # The support person who works on the ticket
    assigned_id = fields.Many2one('res.users', string='Assigned To', tracking=True)

    priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority', default='1', tracking=True,
    )
    category = fields.Selection(
        [
            ('hardware', 'Hardware'),
            ('software', 'Software'),
            ('network', 'Network'),
            ('other', 'Other'),
        ],
        string='Category', default='other',
    )
    stage = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        string='Stage', default='new', tracking=True,
    )
    deadline = fields.Date(string='Deadline')
    # Screenshots or files attached to the ticket
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model_create_multi
    def create(self, vals_list):
        # Give every new ticket the next number from the sequence
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.basic.ticket') or 'New'
        return super().create(vals_list)
