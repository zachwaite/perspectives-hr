odoo.define('trainingapp.widgets', function (require) {
  'use strict';

  var Widget = require('web.Widget');

  var TrainingList = Widget.extend({
    template: 'trainingapp.list',
    events: {},
    custom_events: {},
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options, trainings) {
      this._super.apply(this, arguments);
      this.trainings = trainings;
      console.log(trainings);
    },

  });

  return {
    TrainingList: TrainingList,
  };
});
