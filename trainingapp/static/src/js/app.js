odoo.define('trainingapp.views', function (require) {
  'use strict';

  var Widget = require('web.Widget');
  var TrainingAppSession = require('trainingapp.models').TrainingAppSession;
  var TrainingList = require('trainingapp.widgets').TrainingList;
  var Dashboard = require('trainingapp.widgets').Dashboard;

  require('web.dom_ready');

  var TrainingApp = Widget.extend({
    template: 'trainingapp.app',
    events: {},
    custom_events: {
      'filter-list': '_filterList',
    },
    xmlDependencies: ['/trainingapp/static/src/xml/app_views.xml'],

    init: function (parent, options) {
      console.log('TrainingApp.init()');
      this._super.apply(this, arguments);
      this.session = new TrainingAppSession(odoo.session_info.user_id);
      var self = this;
      // specify the anchors for the child widgets
      this.listElem = '.o_training_list';
      this.dashboardElem = '.o_training_dashboard';
    },

    willStart: function () {
      console.log('TrainingApp.willStart()');
      var self = this;
      return $.when(
        this._super.apply(this, arguments),
        this.session.fetchUserInfo(),
        this.session.fetchAppData(),
      );
    },

    start: function () {
      console.log('TrainingApp.start()');
      var self = this;
      return this._super.apply(this, arguments).then(function () {
        self.trainingList = new TrainingList(self, {}, self.session.data.trainings);
        self.trainingList.appendTo($(self.listElem));

        self.dashboard = new Dashboard(self, {}, self.session.data.dashboard);
        self.dashboard.appendTo($(self.dashboardElem));
      });
    },

    /*
     * Filter the accordion based on selection of a card
     */
    _filterList: function (e) {
      console.log('TrainingApp._filter()');
      var key = e.data.key;
      var self = this;
      var filteredTrainings = self.session.filterTrainings(key);
      self.trainingList.trainings = filteredTrainings;
      self.trainingList._render();
    },

  });

  var $elem = $('.o_app_content');
  var app = new TrainingApp(null);
  app.appendTo($elem);
});
