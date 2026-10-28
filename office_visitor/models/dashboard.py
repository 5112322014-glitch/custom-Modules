from datetime import timedelta

from odoo import api, fields, models


class OfficeVisitorDashboard(models.Model):
    _inherit = 'office.visitor'

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        date_from = today - timedelta(days=10)

        inside = self.search([('state', '=', 'checked_in')])
        inside_list = []
        for visitor in inside:
            check_in = ''
            if visitor.check_in_time:
                local_time = fields.Datetime.context_timestamp(
                    self, visitor.check_in_time)
                check_in = local_time.strftime('%H:%M')
            inside_list.append({
                'id': visitor.id,
                'name': visitor.name,
                'place': visitor.place,
                'host': visitor.sudo().host_employee_id.name or '',
                'check_in': check_in,
            })

        daily = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            daily.append({
                'label': day.strftime('%a %d'),
                'date': str(day),
                'count': self.search_count([('visit_date', '=', day)]),
            })
        max_count = max([d['count'] for d in daily] + [1])
        for d in daily:
            d['percent'] = int(d['count'] * 100 / max_count)

        return {
            'today': str(today),
            'date_from': str(date_from),
            'today_count': self.search_count([('visit_date', '=', today)]),
            'inside_count': len(inside),
            'checked_out_today': self.search_count([
                ('state', '=', 'checked_out'),
                ('visit_date', '=', today)]),
            'last_10_days': self.search_count([
                ('visit_date', '>=', date_from)]),
            'daily': daily,
            'inside_list': inside_list,
        }
