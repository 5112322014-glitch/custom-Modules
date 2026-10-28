from odoo import api, fields, models


class BasicForm(models.Model):
    # Technical name of the model (the database table will be basic_form)
    _name = 'basic.form'
    _description = 'Basic Form'

    # Basic details
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    notes = fields.Text(string='Notes')

    # Employee details
    job_title = fields.Char(string='Job Title')
    department = fields.Selection(
        [
            ('sales', 'Sales'),
            ('it', 'IT'),
            ('hr', 'HR'),
            ('finance', 'Finance'),
            ('other', 'Other'),
        ],
        string='Department',
    )
    joining_date = fields.Date(string='Joining Date')
    # Profile photo, resized to a small size to save space
    image = fields.Image(string='Photo', max_width=256, max_height=256)

    # Files attached to this record (CV, ID copy, etc.)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    # New fields
    employee_id = fields.Char(string='Employee ID', copy=False, readonly=True)
    employment_type = fields.Selection(
        [
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
            ('intern', 'Intern'),
        ],
        string='Employment Type',
        default='full_time',
    )
    status = fields.Selection(
        [
            ('active', 'Active'),
            ('on_leave', 'On Leave'),
            ('resigned', 'Resigned'),
        ],
        string='Status',
        default='active',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender',
    )
    address = fields.Text(string='Address')
    work_location = fields.Char(string='Work Location')
    # Link to another employee record (the manager of this employee)
    manager_id = fields.Many2one('basic.form', string='Manager')
    salary = fields.Float(string='Salary')

    @api.model_create_multi
    def create(self, vals_list):
        # Give every new employee the next number from the sequence
        for vals in vals_list:
            if not vals.get('employee_id'):
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('basic.form.employee')
        return super().create(vals_list)
