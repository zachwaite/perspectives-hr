from collections import OrderedDict
from operator import itemgetter

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem

from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values['return_demo_count'] = request.env['hr.evaluation.demonstration'].search_count([
            '|',
               '&', ('eligible_evaluators_user_ids', 'in', request.env.user.id), ('is_closed', '=', False),
               '&', ('eligible_employees_user_ids', 'in', request.env.user.id), ('is_closed', '=', False)
        ])
        return values

    def _return_demo_get_page_view_values(self, return_demo, access_token, **kwargs):
        values = {
            'page_name': 'return_demo',
            'return_demo': return_demo,
        }
        return self._get_page_view_values(return_demo, access_token, values, 'my_return_demos_history', False, **kwargs)

    @http.route(['/my/return_demos', '/my/return_demos/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_return_demos(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        ReturnDemo = request.env['hr.evaluation.demonstration']
        domain = [('is_closed', '=', False)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('hr.evaluation.demonstration', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        return_demo_count = ReturnDemo.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/return_demos",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=return_demo_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        return_demos = ReturnDemo.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_return_demos_history'] = return_demos.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'return_demos': return_demos,
            'page_name': 'return_demo',
            'archive_groups': archive_groups,
            'default_url': '/my/return_demos',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("hr_competency_base.portal_my_return_demos", values)

    @http.route(['/my/return_demo/<int:return_demo_id>'], type='http', auth="public", website=True)
    def portal_my_return_demo(self, return_demo_id=None, access_token=None, **kw):
        try:
            return_demo_sudo = self._document_check_access('hr.evaluation.demonstration', return_demo_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._return_demo_get_page_view_values(return_demo_sudo, access_token, **kw)

        if request.env.user.id in values['return_demo'].eligible_evaluators_user_ids.ids:
            values['user_is_evaluator'] = True
            values['request_user_id'] = request.env.user.id
        return request.render("hr_competency_base.portal_my_return_demo", values)

