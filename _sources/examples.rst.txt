Examples
========

Basic
-----

To get started - make sure your printer is on the same network as your target machine.
Make sure that ports 8883, 6000 and 990 are accessible from your machine. 

.. literalinclude:: ../examples/Basic/basic.py
  :language: python

Basic No Camera
---------------

If using the api without camera connection follow the below example.
Note that camera on X1 machines is not supported on the API for versions less
than 2.7.0

.. literalinclude:: ../examples/Basic/basic_no_camera.py
  :language: python


Basic Subscription
------------------

A simple looping subscription script to get you started once you've been able to connect the printer up to the api.

.. literalinclude:: ../examples/Basic/basic_subscription.py
  :language: python

Get a Camera Frame
------------------

Access the Camera of a P1 printer:

.. literalinclude:: ../examples/camera/camera.py
  :language: python

Start a Print
-------------

Start a print using the api given a valid gcode file:

.. literalinclude:: ../examples/print/print_gcode.py
  :language: python
