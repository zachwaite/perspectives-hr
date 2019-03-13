odoo.define('trainingapp.widgets', function (require) {
  'use strict';

  var Widget = require('web.Widget');

  var Dashboard = Widget.extend({
    template: 'trainingapp.dashboard',
    events: {},
    custom_events: {},
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options, stats) {
      console.log('Dashboard.init()');
      this._super.apply(this, arguments);
      this.stats = stats;
    },
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
      console.log(trainings);
    },

  });

  return {
    TrainingList: TrainingList,
    Dashboard: Dashboard,
  };
});
