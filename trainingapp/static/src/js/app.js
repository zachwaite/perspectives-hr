odoo.define('trainingapp.views', function (require) {
  'use strict';

  var Widget = require('web.Widget');
  var User = require('trainingapp.models').User;
  //var TrainingDashboard = require('trainingapp.widgets').TrainingDashboard;
  var TrainingList = require('trainingapp.widgets').TrainingList;

  require('web.dom_ready');

  var TrainingApp = Widget.extend({
    template: 'trainingapp.app',
    events: {},
    custom_events: {},
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options) {
      console.log('TrainingApp.init()');
      this._super.apply(this, arguments);
      this.user = new User({id: odoo.session_info.user_id});
      var self = this;
      this.$dashboardElem = $('.o_training_dashboard');
      this.listElem = '.o_training_list';
    },

    willStart: function () {
      console.log('TrainingApp.willStart()');
      var self = this;
      return $.when(
        this._super.apply(this, arguments),
        // set this.user.info
        this.user.fetchUserInfo(),
        // set this.user.trainings
        this.user.fetchCategorizedTrainings(),
      );
    },

    start: function () {
      console.log('TrainingApp.start()');
      var self = this;
      return this._super.apply(this, arguments).then(function () {
        self.trainingList = new TrainingList(self, {}, self.user.trainings);
        self.trainingList.appendTo($(self.listElem));
      });
    },

  });

  var $elem = $('.o_app_content');
  var app = new TrainingApp(null);
  app.appendTo($elem);
});
