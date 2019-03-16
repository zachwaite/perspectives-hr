odoo.define('trainingapp.widgets', function (require) {
  'use strict';

  var core = require('web.core');
  var qweb = core.qweb;
  var Widget = require('web.Widget');

  var Dashboard = Widget.extend({
    template: 'trainingapp.dashboard',
    events: {
      'click .o_training_card': '_setFilter',
    },
    custom_events: {},
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options, stats) {
      console.log('Dashboard.init()');
      this._super.apply(this, arguments);
      this.stats = stats;
    },

    _setFilter: function (e) {
      $('.o_training_card').removeClass('active');
      $('.fa-check-circle').addClass('d-none');
      $(e.target.closest('.o_training_card')).addClass('active');
      $(e.target.closest('.o_training_card')).find('i.fa-check-circle').removeClass('d-none');
      var key = $(e.target.closest('.o_training_card')).find('input.o_filter_key').val();
      this.trigger_up('filter-list', {key: key});
    }

  });

  var TrainingList = Widget.extend({
    template: 'trainingapp.list',
    events: {},
    custom_events: {},
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options, trainings) {
      console.log('TrainingList.init()');
      this._super.apply(this, arguments);
      this.trainings = trainings;
    },

    _render: function () {
      this.renderElement();
    },

  });

  return {
    TrainingList: TrainingList,
    Dashboard: Dashboard,
  };
});
