# © 2018 Waite Perspectives, LLC - Zach Waite
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class ActivePeriodMixin(models.AbstractModel):
    """Utility mixin to provide a standard way to
    deactivate and filter records based on some
    availability timeframe.
    """
    _name = 'base.active_period.mixin'
    _description = 'Active Period Mixin'

    active = fields.Boolean(
        string=_('Active'),
        default=True,
    )

    available_on = fields.Date(
        string=_('Available On'),
        default=fields.Date.today(),
    )

    available_until = fields.Date(
        string=_('Available Until'),
    )

    def get_preavailable_records(self):
        return self.filtered(
            lambda r: r.available_on and r.available_on > datetime.date.today()
        )

    def get_expired_records(self):
        return self.filtered(
            lambda r: r.available_until and r.available_until < datetime.date.today()
        )

    @api.multi
    def set_expired_inactive(self):
        expired = self.get_expired_records()
        _logger.info('Archiving records: %s' % expired)
        return expired.write({'active': False})

    @api.model
    def _cron_deactivate_expired_records(self, models):
        # best to explicitly pass models to deactivate
        for model in models:
            SudoRS = self.env[model].sudo().search([])
            SudoRS.set_expired_inactive()
        return True

