.. couchquery documentation master file, created by
   sphinx-quickstart on Mon Aug 17 21:05:22 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tesbot -- Test Automation and Distribution System
=================================================

.. module:: testbot
   :synopsis: Test Automation and Distribution System.
.. moduleauthor:: Mikeal Rogers <mikeal.rogers@gmail.com>
.. sectionauthor:: Mikeal Rogers <mikeal.rogers@gmail.com>

Testbot is a continuous integration server and client for distributing and running tests. It uses simple REST and JSON interfaces so that it can be easily extensible.

.. toctree::
   :maxdepth: 3

.. _installation:

Installation
------------

`testbot` requires `setuptools <http://pypi.python.org/pypi/setuptools>`_, `mako <http://www.makotemplates.org/>`_, `couchquery <http://github.com/mikeal/couchquery>`_, `webenv <http://github.com/mikeal/webenv>`_. If you do not have setuptools installed already you will want to::

   $ curl -O http://peak.telecommunity.com/dist/ez_setup.py
   $ python ez_setup.py

Now you can install testbot, easy_install will handle installing the other dependencies::

   $ easy_install testbot

The source code is publicly `available on github <http://github.com/mikeal/testbot>`_. Tickets should be logged on the `github issues tracker <http://github.com/mikeal/testbot/issues>`_. 

The process for code contributions is for users to `fork the repository on github <http://help.github.com/forking/>`_, push modifications to their public fork, and then send `mikeal <http://github.com/mikeal>`_ a `pull request <http://github.com/guides/pull-requests>`_.

.. _creating-a-client:

Creating a client
-----------------

The easiest way to write a client is to subclass :class:`Client` ::

   from testbot.client import Client

   class MyClient(Client):
       jobtypes = ['my-test-type']
   
       def do_job(self, job):
           # Job handler
           return {"result":False, "debug":"We should write code that actually handles this job"}

You can now start the client. If you would like to block indefinitely you can call :class:`Client.run()`, if you would like to start a background thread to handle jobs you can use :class:`Client.start()`. If you start a Client instance using :class:`Client.start()` you can stop it using :class:`Client.stop()`. Calling :class:`Client.stop()` will block until the current do_job call finishes if one is currently running.

Clients register with the testbot server, by default they create an attribute called `capabilities` which includes two other attributes, `platform` and `jobtypes`. In the example above only `jobtypes` is defined because by default :class:`Client` will pull platform information out of the Python interpreter which works for most clients but not all. For instance, here is a client that supports a mobile platform that might be tethered to a machine that is running this code. ::

   class MobileClient(MyClient):
       jobtypes = ['mobile-unittest']
       platform = {'name':'Nokia N900', 'os.name':'Maemo', 'os.version':'4.1.0'}

If necessary, you can even override the entire capabilities attribute if you need to support a more customized configuration. ::

   import os
   sysname, nodename, release, version, machine = os.uname()

   class MultiPythonClient(MyClient):
       capabilities = {'jobtypes':'python-unittest',
                       'platforms': [{'os.name':sysname,
                                      'os.version':version,
                                      'python.version':'2.5.1',
                                     },
                                     {'os.name':sysname,
                                      'os.version':version,
                                      'python.version':'2.6.2',
                                     }]
                       }

The example is a client that can run Python unittests on multiple versions of Python by making shell calls out to different Python binaries. The server will be able to use this information when assigning jobs to this client.

After the client is registered it starts sending a heartbeat every 60 seconds (this is configurable). In it's heartbeat it sends all the information it can about the client's current state. Your client instance will have an attribute called `client_info` which you can add status and debugging information to that will be reported to the server in every heartbeat. ::

   class MyClient(Client):
       def do_job(self, job):
           resp, content = httplib2.Http().request('http://www.facebook.com')
           if resp.status != 200:
               self.client_info['firewall_info'] = 'Inside some crap corporate network'

If you don't want to wait for the next heartbeat to come around you can push this information immediately using :meth:`Client.push_status`. ::

    self.client_info['firewall_info'] = 'Inside some crap corporate network'
    self.push_status()

Any information you like can be added to `client_info` but one of the more useful things you can modify is information about the current job. Before :meth:`Client.do_job` is called it adds the current job to client_info. Any modifications you make to that job will also be sent in the next heartbeat. ::

    self.client_info['firewall_info'] = 'Inside some crap corporate network'
    self.client_info['job']['firewall_info'] = 'Test was run inside a corporate network'

Since testbot uses JSON as it's data format all the different objects are extensible.
