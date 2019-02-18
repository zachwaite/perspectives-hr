==============================================
Manage Complex Employee Training Requirements
==============================================

This is the base model for the hr_competency stack. It provides data structures,
minimal views and logic to:

* Manage competency requirements and their lifecycle
* Manage evaluations as either self administered quizzes (knowledge tests) or
  proctored evaluations administered by another employee (return demonstrations)
* Manage evaluation results as either survey responses, manual uploads or credit
  vouchers (i.e. 3rd party certs, diplomas)
* Compute evaluation scores and award credits based on score
* Manage groups of competency requirements and corresponding assignment criteria
  using templates
* Manage employee training plans by associating templates to a training plan
* Offer content and evaluations to appropriate users based on their training
  plan through the portal

TODO
------

* Replace stored fields with _search param and search fn where able
* Add special Competency Requirement <Education> to everything by default for
use in requirements that sum total credit hours.

* Documentation
* Tests
* Demo data

Extension Modules
------------------

* Electronic Signatures for Training
* Text Alerts
* Audit trail and notifications through the discuss app

