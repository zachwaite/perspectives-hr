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
        values['knowledge_test_count'] = request.env['hr.evaluation.knowledge'].search_count([
            ('eligible_evaluators_user_ids', 'in', request.env.user.id),
            ('survey_id.stage_id.closed', '=', False),
        ])
        return values

    def _knowledge_test_get_page_view_values(self, knowledge_test, access_token, **kwargs):
        values = {
            'page_name': 'knowledge_test',
            'knowledge_test': knowledge_test,
        }
        return self._get_page_view_values(knowledge_test, access_token, values, 'my_knowledge_tests_history', False, **kwargs)

    @http.route(['/my/knowledge_tests', '/my/knowledge_tests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_knowledge_tests(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        KnowledgeTest = request.env['hr.evaluation.knowledge']
        domain = [('survey_id.stage_id.closed', '=', False)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('hr.evaluation.knowledge', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        knowledge_test_count = KnowledgeTest.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/knowledge_tests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=knowledge_test_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        knowledge_tests = KnowledgeTest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_knowledge_tests_history'] = knowledge_tests.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'knowledge_tests': knowledge_tests,
            'page_name': 'knowledge_test',
            'archive_groups': archive_groups,
            'default_url': '/my/knowledge_tests',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("hr_competency_base.portal_my_knowledge_tests", values)

    @http.route(['/my/knowledge_test/<int:knowledge_test_id>'], type='http', auth="public", website=True)
    def portal_my_knowledge_test(self, knowledge_test_id=None, access_token=None, **kw):
        try:
            knowledge_test_sudo = self._document_check_access('hr.evaluation.knowledge', knowledge_test_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._knowledge_test_get_page_view_values(knowledge_test_sudo, access_token, **kw)

        if request.env.user.id in values['knowledge_test'].eligible_evaluators_user_ids.ids:
            values['user_is_evaluator'] = True
            values['request_user_id'] = request.env.user.id
        return request.render('hr_competency_base.portal_my_knowledge_test', values)

