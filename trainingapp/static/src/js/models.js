odoo.define('trainingapp.models', function (require) {
  'use strict';

  var Class = require('web.Class');
  var rpc = require('web.rpc');

  var Training = Class.extend({
    init: function (vals) {
      console.log('Training.init()');
      Object.assign(this, vals);
    },
  });

  var User = Class.extend({
    init: function (values) {
      console.log('User.init()');
      Object.assign(this, values);
      this.trainings = [];
      this.dashboard = false;
    },

    fetchUserInfo: function () {
        console.log('User.fetchUserInfo()');
        var self = this;
        return rpc.query({
            model: 'res.users',
            method: 'read',
            args: [[this.id]],
            kwargs: {fields: ['id', 'login', 'name', 'image_small', 'partner_id']}
        }).then(function (values) {
            // just to unnest I think
            var _values = values[0];
            _values.partner_id = _values.partner_id[0];
            Object.assign(self, _values);
            return self;
        });
    },

    fetchAllTrainings: function () {
      var self = this;
      return rpc.query({
        model: 'hr.training.plan.detail',
        method: 'search_read',
        args: [[]],
        kwargs: {fields: ['id', 'name']}
      }).then(function (training_vals) {
        for (var vals of training_vals) {
          self.trainings.push(new Training(vals));
        }
        return self;
      });
    },

    fetchCategorizedTrainings: function () {
      console.log('User.fetchCategorizedTrainings()');
      var self = this;
      return rpc.query({
        model: 'hr.training.plan.detail.categorized',
        method: 'search_read',
        args: [[]],
        kwargs: {fields: ['id', 'employee_id', 'training_plan_detail_id', 'training_plan_detail_name', 'competency_requirement_id', 'competency_requirement_name']}
      }).then(function (training_vals) {
        for (var vals of training_vals) {
          self.trainings.push(new Training(vals));
        }
        return self;
      });
    },

    fetchDashboardData: function () {
      console.log('User.fetchDashboardData()');
      var self = this;
      return rpc.query({
        route: '/training/dashboard',
        args: [[]],
        kwargs: {user_id: self.id}
      }).then(function (dashboard_data) {
        self.dashboard = dashboard_data;
      });
    },

  });

  return {
    Training: Training,
    User: User,
  };
});
