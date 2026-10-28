import secrets
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request

TOKEN_VALID_HOURS = 24


def _json(data, status=200):
    return request.make_json_response(data, status=status)


def _error(message, status=400):
    return _json({'success': False, 'error': message}, status)


def _get_body():
    try:
        return request.get_json_data() or {}
    except Exception:
        return {}


def _get_user_env():
    """Return an environment bound to the token's user, or None."""
    header = request.httprequest.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token_value = header[7:].strip()
    token = request.env(su=True)['office.visitor.token'].search([
        ('token', '=', token_value),
        ('expires_at', '>', fields.Datetime.now()),
    ], limit=1)
    if not token:
        return None
    return request.env(user=token.user_id.id)


def _serialize(rec):
    employee = rec.sudo().host_employee_id
    return {
        'id': rec.id,
        'badge_number': rec.badge_number,
        'name': rec.name,
        'place': rec.place,
        'reason': rec.reason,
        'host_employee': {'id': employee.id, 'name': employee.name},
        'visit_date': str(rec.visit_date) if rec.visit_date else None,
        'check_in_time': str(rec.check_in_time) if rec.check_in_time else None,
        'check_out_time': str(rec.check_out_time) if rec.check_out_time else None,
        'state': rec.state,
    }


class OfficeVisitorAPI(http.Controller):

    # 1) Login and get a token
    @http.route('/api/visitor/login', type='http', auth='none',
                methods=['POST'], csrf=False)
    def api_login(self, **kwargs):
        data = _get_body()
        login = data.get('login')
        password = data.get('password')
        if not login or not password:
            return _error('login and password are required', 400)
        try:
            auth_info = request.env(su=True)['res.users'].authenticate(
                request.db,
                {'login': login, 'password': password, 'type': 'password'},
                {'interactive': False},
            )
        except AccessDenied:
            return _error('Invalid login or password', 401)

        expires_at = fields.Datetime.now() + timedelta(hours=TOKEN_VALID_HOURS)
        token_value = secrets.token_urlsafe(32)
        request.env(su=True)['office.visitor.token'].create({
            'token': token_value,
            'user_id': auth_info['uid'],
            'expires_at': expires_at,
        })
        return _json({
            'success': True,
            'token': token_value,
            'token_type': 'Bearer',
            'expires_at': str(expires_at),
        })

    # Helper: list employees (to get host_employee_id)
    @http.route('/api/visitor/employees', type='http', auth='none',
                methods=['GET'], csrf=False)
    def api_employees(self, **kwargs):
        env = _get_user_env()
        if env is None:
            return _error('Invalid or expired token', 401)
        employees = env['hr.employee'].sudo().search_read([], ['name'])
        return _json({'success': True, 'count': len(employees),
                      'employees': employees})

    # 2) List of visitors (default: last 10 days)
    @http.route('/api/visitor/list', type='http', auth='none',
                methods=['GET'], csrf=False)
    def api_list(self, days=10, state=None, **kwargs):
        env = _get_user_env()
        if env is None:
            return _error('Invalid or expired token', 401)
        try:
            days = int(days)
        except ValueError:
            return _error('days must be a number', 400)
        Visitor = env['office.visitor']
        date_from = fields.Date.context_today(Visitor) - timedelta(days=days)
        domain = [('visit_date', '>=', date_from)]
        if state:
            domain.append(('state', '=', state))
        visitors = Visitor.search(domain)
        return _json({
            'success': True,
            'count': len(visitors),
            'visitors': [_serialize(v) for v in visitors],
        })

    # 3) Add a new visitor
    @http.route('/api/visitor/create', type='http', auth='none',
                methods=['POST'], csrf=False)
    def api_create(self, **kwargs):
        env = _get_user_env()
        if env is None:
            return _error('Invalid or expired token', 401)
        data = _get_body()
        missing = [f for f in ('name', 'place', 'reason', 'host_employee_id')
                   if not data.get(f)]
        if missing:
            return _error('Missing fields: ' + ', '.join(missing), 400)
        try:
            employee_id = int(data['host_employee_id'])
        except (TypeError, ValueError):
            return _error('host_employee_id must be a number', 400)
        if not env['hr.employee'].sudo().browse(employee_id).exists():
            return _error('Employee not found', 404)
        try:
            visitor = env['office.visitor'].create({
                'name': data['name'],
                'place': data['place'],
                'reason': data['reason'],
                'host_employee_id': employee_id,
            })
        except UserError as e:
            return _error(str(e), 403)
        return _json({'success': True, 'visitor': _serialize(visitor)}, 201)

    # 4) Check in
    @http.route('/api/visitor/<int:visitor_id>/check_in', type='http',
                auth='none', methods=['POST'], csrf=False)
    def api_check_in(self, visitor_id, **kwargs):
        return self._run_action(visitor_id, 'action_check_in')

    # 5) Check out
    @http.route('/api/visitor/<int:visitor_id>/check_out', type='http',
                auth='none', methods=['POST'], csrf=False)
    def api_check_out(self, visitor_id, **kwargs):
        return self._run_action(visitor_id, 'action_check_out')

    def _run_action(self, visitor_id, method_name):
        env = _get_user_env()
        if env is None:
            return _error('Invalid or expired token', 401)
        visitor = env['office.visitor'].browse(visitor_id).exists()
        if not visitor:
            return _error('Visitor not found', 404)
        try:
            getattr(visitor, method_name)()
        except UserError as e:
            return _error(str(e), 400)
        return _json({'success': True, 'visitor': _serialize(visitor)})
