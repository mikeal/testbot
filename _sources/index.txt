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



