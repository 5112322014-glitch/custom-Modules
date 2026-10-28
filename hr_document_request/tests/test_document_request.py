from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrDocumentRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        group_user = cls.env.ref('base.group_user')
        group_hr_manager = cls.env.ref('hr.group_hr_manager')

        # Do normal employees (A aur B) aur ek HR Manager
        cls.user_a = Users.create({
            'name': 'Employee A', 'login': 'emp_a_test',
            'email': 'emp_a@test.com',
            'groups_id': [(6, 0, [group_user.id])],
        })
        cls.user_b = Users.create({
            'name': 'Employee B', 'login': 'emp_b_test',
            'email': 'emp_b@test.com',
            'groups_id': [(6, 0, [group_user.id])],
        })
        cls.hr_manager = Users.create({
            'name': 'HR Manager Test', 'login': 'hr_mgr_test',
            'email': 'hr_mgr@test.com',
            'groups_id': [(6, 0, [group_user.id, group_hr_manager.id])],
        })

        cls.emp_a = cls.env['hr.employee'].create({
            'name': 'Employee A', 'user_id': cls.user_a.id,
        })
        cls.emp_b = cls.env['hr.employee'].create({
            'name': 'Employee B', 'user_id': cls.user_b.id,
        })

        cls.Request = cls.env['hr.document.request']

    def _make_request(self, employee, user=None):
        """Helper: request banata hai (default HR Manager ki taraf se)."""
        user = user or self.hr_manager
        return self.Request.with_user(user).create({
            'employee_id': employee.id,
            'document_type': 'salary_certificate',
            'reason': 'Bank account opening',
            'required_by_date': fields.Date.today() + timedelta(days=5),
        })

    # 1. Sequence
    def test_01_sequence(self):
        req1 = self._make_request(self.emp_a)
        req2 = self._make_request(self.emp_a)
        self.assertNotEqual(req1.name, 'New', "Reference sequence se bana hona chahiye")
        self.assertNotEqual(req2.name, 'New')
        self.assertNotEqual(req1.name, req2.name, "Har request ka reference alag hona chahiye")

    # 2. Teen submitted requests ki limit
    def test_02_max_three_submitted_requests(self):
        reqs = [self._make_request(self.emp_a) for _i in range(4)]
        for req in reqs[:3]:
            req.action_submit()
            self.assertEqual(req.state, 'submitted')
        with self.assertRaises(ValidationError):
            reqs[3].action_submit()
        # Doosre employee par is limit ka asar nahi
        other = self._make_request(self.emp_b)
        other.action_submit()
        self.assertEqual(other.state, 'submitted')

    # 3. Issued lock
    def test_03_issued_lock(self):
        req = self._make_request(self.emp_a)
        req.action_submit()
        req_mgr = req.with_user(self.hr_manager)
        req_mgr.action_approve()
        req_mgr.write({
            'document_attachment': 'SGVsbG8=',  # base64 "Hello"
            'attachment_filename': 'letter.pdf',
        })
        req_mgr.action_issue()
        self.assertEqual(req.state, 'issued')

        # Business field edit blocked
        with self.assertRaises(UserError):
            req_mgr.write({'reason': 'Changed after issue'})

        # Chatter ab bhi chalni chahiye
        req_mgr.message_post(body="Note after issue")

        # Normal employee reopen nahi kar sakta
        with self.assertRaises(AccessError):
            req.with_user(self.user_a).action_reopen()

        # HR Manager reopen kar sakta hai, phir edit chalti hai
        req_mgr.action_reopen()
        self.assertEqual(req.state, 'approved')
        req_mgr.write({'reason': 'Typo fixed'})
        self.assertEqual(req.reason, 'Typo fixed')

    # 4. Record rule
    def test_04_record_rule(self):
        # HR ne dono employees ke liye requests banayi (create_uid = HR)
        req_a = self._make_request(self.emp_a)
        req_b = self._make_request(self.emp_b)

        # Employee A ko sirf apni request dikhe, chahe HR ne banayi ho
        visible_a = self.Request.with_user(self.user_a).search([])
        self.assertIn(req_a, visible_a)
        self.assertNotIn(req_b, visible_a)

        # A, B ki request read nahi kar sakta
        with self.assertRaises(AccessError):
            req_b.with_user(self.user_a).read(['name'])

        # HR Manager ko dono dikhein
        visible_hr = self.Request.with_user(self.hr_manager).search(
            [('id', 'in', (req_a | req_b).ids)])
        self.assertEqual(visible_hr, req_a | req_b)

    # 5. Approve ka server-side check
    def test_05_approve_requires_hr_manager(self):
        req = self._make_request(self.emp_a)
        req.action_submit()
        with self.assertRaises(AccessError):
            req.with_user(self.user_a).action_approve()
        self.assertEqual(req.state, 'submitted')
