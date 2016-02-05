# MainTraq
__A Maintenance Tracker. Andela Kenya Class V Boot Camp Project.__

__MainTraq__ (from Maintenance Tracker) is an online maintenance/repairs requests
tracker that keeps record of maintenance tasks requested by its users within a
particular facility.
It provides a platform where a user can file a maintenance request online and
obtain feedback about the same from the facility admin.
The **facility** can be (but not limited to) an organisation or an
organisation's department.

__MainTraq__ is written in Python by leveraging the the [Flask microframework.](http://flask.pocoo.org/ Flask's Homepage)
with its UI primarily being rendered by the `Jinja2` templating engine.

## Main Features
* Allow users to request for maintenance
* Allow users update descriptions of their requests
* Notify users of changes in status of their request
* Allow facility admins assign tasks to maintenance crew
* Allow maintenance crew update the status of assigned tasks
* Provide user authentication and password recovery functions
* Provide email notifications to users once their requests are fulfilled

## Getting Started
You can view the project's live demo [hosted up on Heroku.](maintraq.herokuapp.com)

**NOTE:** Access to the site will require you to sign up.

Alternatively, you can easily get a local copy of this application on your workstation.
This guide assumes that you have a working installation of `Python 3.4` and
`pip` in your workstation

1. Clone this repository

   `$ git clone https://github.com/Waiyaki/maintraq.git`

2. Install project dependencies via `pip`. It's recommended that you do this in a `virtualenv`

    `$ pip install -r requirements.txt`

3. Initialize your development database.

    `$ python manage.py db init`

4. Construct the database and migrate the database models.

    `$ python manage.py db upgrade`

5. Run a development server.

    `$ python manage.py runserver`

### Configurations
If you are developing or deploying __MainTraq__, it will expect the following
environment variables:
* `MAINTRAQ_ADMIN` - The email address of the system administrator.
  When the administrator (user with this email) signs up in the registration page, the system will
  automatically assign them the admin role.
* `SECRET_KEY` - This will be the key used to generate authentication tokens as well as the `csrf` tokens.
* `MAIL_USERNAME` - This will be the email address used by the system to send out emails to it's users.
* `MAIL_PASSWORD` - The password to the aforementioned `MAIL_USERNAME`

Aside from those, more configuration settings can be found in the [config.py](https://github.com/Waiyaki/maintraq/blob/master/config.py) file and can be customised to fit a particular case.

### Workflow
Once a user signs up in __MainTraq__, the system will require them to confirm
their account by email verification, after which the user will be able to
access the maintenance requests form.
Once a user requests for maintenance, the designated system `admin` will be
notified of the new task request. The `admin` will then either choose to accept
the request or reject it. Whichever decision the `admin` makes, it will be sent
to the user via email as feedback for that request.
If the `admin` chooses to accept the request, they will assign a `maintenance staff
member` to the task. `maintenance staff member`s also receive email notifications about new
assignments.
A `maintenance staff member` has access to the task they are performing and can
update the task's progress.
The `admin` is notified if any task is marked as done, so that they may mark it as
`resolved`. If a task is resolved, the user who requested it gets an email notification.

### Improvements
* Currently, the system threads sending of email notifications. This is still, unfortunately,
  not sufficient if the system has to send several emails. For example, if the `admin` updates
  a request and accepts it and in the same update assigns a `maintenance staff member` to the
  task, the user (`admin`, in this case) might notice a slight lag in the system's response.
  This situation can be improved by using a `message broker`, e.g `celery` to schedule and
  send out those emails asynchronously without holding the systems response.
* The `maintenance staff members` currently receive notifications via email. It would be better
  if they received those notifications on their mobile phones since not all of them are
  expected to have access to their mailboxes at all times. Integration with an SMS API, like
  `Twilio` or `Africa's Talking` would resolve this issue.
* If a `message broker` was integrated into the system, it could also be used to keep track
  of `in progress` tasks and send out friendly reminders to the `maintenance staff member`
  assigned to that task if it was taking too long.
* Ideally, the system should also provide a way for the `admin` to reject the task's resolution
  in the case where a `maintenance staff member` does not accomplish that task correctly.
* The user should be able to upload some photos of what's broken, if they choose to.
  This feature is currently not implemented.

All of the aforementioned improvements are currently in the `icebox` and are viewable in this [Trello Board.](https://trello.com/b/BJfAL79J/maintenance-tracker)

#### BUGS
* The page redirected to when the user is unconfirmed breaks at times.

### Conclusion
Since this project is being used as part of a learning process, it's only fair I mention
what I have learnt from it.
* How to perform user authentication using Flask
* How to leverage the `Jinja2` templating framework to write composable and reusable
  HTML templates using `macros`
* How to process server requests and perform the requested action using Flask
* How to extend Flask's functionality by leveraging the Flask extensions.
* How to send asynchronous emails
* I learnt about non-blocking message brokers that can be used to perform asynchronous
  tasks or tasks that should be run as `cron` jobs
