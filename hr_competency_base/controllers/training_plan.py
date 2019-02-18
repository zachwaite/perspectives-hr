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
        values['training_plan'] = request.env['hr.training.plan'].search([
            ('employee_id', 'in', request.env.user.employee_ids.ids),
        ])
        values['training_plan_detail_count'] = len(values['training_plan'].training_plan_detail_ids)
        return values

    def _training_plan_detail_get_page_view_values(self, training_plan_detail, access_token, **kwargs):
        values = {
            'page_name': 'training_plan_detail',
            'training_plan_detail': training_plan_detail,
        }

        # TODO: Refactor
        available_knowledge_tests = request.env['hr.evaluation.knowledge'].search([
            ('eligible_evaluator_ids', 'in', request.env.user.employee_ids.ids),
            ('competency_requirement_ids', 'in', training_plan_detail.training_plan_template_detail_id.competency_requirement_id.id),
            ('is_closed', '=', False),
        ])

        qualifying_competency_results = training_plan_detail.qualifying_results_ids.filtered(
            lambda rs: rs.result_type == 'evaluation'
        )

        # handles knowledge test and return demo
        qualifying_evaluation_results = request.env['hr.competency.result.evaluation'].sudo().search([
            ('competency_result_id', 'in', qualifying_competency_results.ids),
        ])
        qualifying_evaluation_results_evaluations = qualifying_evaluation_results.mapped('evaluation_id')
        available_return_demos = request.env['hr.evaluation.demonstration'].search([
            ('eligible_employee_ids', 'in', request.env.user.employee_ids.ids),
            ('competency_requirement_ids', 'in', training_plan_detail.training_plan_template_detail_id.competency_requirement_id.id),
            ('is_closed', '=', False),
        ])

        values.update({
            'available_knowledge_tests': available_knowledge_tests,
            'available_return_demos': available_return_demos,
            'qualifying_evaluation_results_evaluations': qualifying_evaluation_results_evaluations,
        })

        return self._get_page_view_values(training_plan_detail, access_token, values, 'my_training_plan_history', False, **kwargs)

    @http.route(['/my/training_plan_details', '/my/training_plan_details/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_training_plan_detail(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        TrainingPlanDetail = request.env['hr.training.plan.detail']
        domain = [('training_plan_id', '=', values['training_plan'].id)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'deadline': {'label': _('Next Due'), 'order': 'date_deadline'},
        }
        if not sortby:
            sortby = 'deadline'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('hr.training.plan.detail', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        training_plan_detail_count = TrainingPlanDetail.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/training_plan_details",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=training_plan_detail_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        training_plan_details = TrainingPlanDetail.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_training_plan_details_history'] = training_plan_details.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'training_plan_details': training_plan_details,
            'page_name': 'training_plan_detail',
            'archive_groups': archive_groups,
            'default_url': '/my/training_plan_details',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("hr_competency_base.portal_my_training_plan_details", values)

    @http.route(['/my/training_plan_detail/<int:training_plan_detail_id>'], type='http', auth="public", website=True)
    def portal_my_training_plan_detail_id(self, training_plan_detail_id=None, access_token=None, **kw):
        try:
            training_plan_detail_sudo = self._document_check_access('hr.training.plan.detail', training_plan_detail_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._training_plan_detail_get_page_view_values(training_plan_detail_sudo, access_token, **kw)

        return request.render('hr_competency_base.portal_my_training_plan_detail', values)

