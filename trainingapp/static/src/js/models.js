odoo.define('trainingapp.models', function (require) {
  'use strict';

  var Class = require('web.Class');
  var rpc = require('web.rpc');
  var ajax = require('web.ajax');

  /**
   * TrainingAppSession is the main object controlling the data
   * it contains the user info, all data used by the widgets
   * and is responsible for communicating with the backend(s)
  
   * Methods that get data from the backend are named fetchXXX
   * Methods that send data to the backend are named postXXX
   * All other methods would be for subsetting data - any transformations
   * should be done server side in the json controllers and any ui manipulation
   * should be performed by the widgets themselves.
   */
  var TrainingAppSession = Class.extend({
    init: function (user_id) {
      console.log('Session.init()');
      this.user_id = user_id;
      this.data = {
        dashboard: false,
        trainings: [],
      };
    },

    filterTrainings: function (key) {
      if (key === 'all') {
        return this.data.trainings;
      } else if (key === 'my') {
        return this.data.trainings.filter(
          t => t.competency_assigned === true
        );
      } else if (key === 'odue') {
        return this.data.trainings.filter(
          t => t.competency_overdue === true
        );
      }
    },

    /**
     * This is the only method that writes to this directly
     * other data fetchers should write to this.data
     */
    fetchUserInfo: function () {
        console.log('Session.fetchUserInfo()');
        var self = this;
        return rpc.query({
            model: 'res.users',
            method: 'read',
            args: [[this.user_id]],
            kwargs: {fields: ['id', 'login', 'name', 'image_small', 'partner_id']}
        }).then(function (values) {
            var _values = values[0];
            _values.partner_id = _values.partner_id[0];
            Object.assign(self, _values);
            return self;
        });
    },

    fetchTrainingData: function () {
      console.log('Session.fetchTrainingData()');
      var self = this;
      var kwargs = {user_id: self.user_id};
      return ajax.jsonRpc(
          '/training/training_data',
          'call',
          kwargs
        ).then(function (records) {
          self.data.trainings = records;
          return self;
        });
    },

    fetchDashboardData: function () {
      console.log('User.fetchDashboardData()');
      var self = this;
      var kwargs = {user_id: self.user_id};
      return ajax.jsonRpc(
          '/training/dashboard',
          'call',
          kwargs
        ).then(function (dashboard_data) {
          self.data.dashboard = dashboard_data;
        });
    },

    /**
     * Encapsulate all data fetches for initialization
     */
    fetchAppData: function () {
      console.log('Session.fetchAppData()');
      var self = this;
      //self.fetchTrainingData();
      self.fetchDashboardData();
    },


  });

  return {
    TrainingAppSession: TrainingAppSession,
  };
});
