#!/usr/bin/env python
"""Setup script for the Vision Egg distribution.
"""
# Copyright (c) 2001, 2002 Andrew Straw.  Distributed under the terms of the
# GNU General Public License (GPL).

from distutils.core import setup, Extension
import sys

extensions = []
is_source_distribution = 0

if len(sys.argv) > 1:
    if sys.argv[1] == 'sdist':
        is_source_distribution = 1

if sys.platform not in ['cygwin','darwin','mac','win32'] or is_source_distribution:
    # The maximum priority stuff should work on most versions of Unix.
    # (It depends on the system call sched_setscheduler.)
    extensions.append(Extension(name='_maxpriority',sources=['src/_maxpriority.c']))

if sys.platform == 'linux2' or is_source_distribution:
    extensions.append(Extension(name='_dout',sources=['src/_dout.c']))

# Normal distutils stuff
setup(name="visionegg",
      version = "0.8.1",
      description = "Vision Egg",
      url = 'http://visionegg.sourceforge.net',
      author = "Andrew Straw",
      author_email = "astraw@users.sourceforge.net",
      licence = "GPL",
      package_dir={'VisionEgg' : 'src',
                   'VisionEgg.test' : 'test',
                   'VisionEgg.demo' : 'demo'},
      packages=[ 'VisionEgg',
                 'VisionEgg.test',
                 'VisionEgg.demo',
                 'VisionEgg.demo.GUI',
                 'VisionEgg.demo.Pyro'],
      ext_package='VisionEgg',
      ext_modules=extensions,
      long_description =
      """The Vision Egg is a programming library (with demo
      applications) that uses standard, inexpensive computer graphics
      cards to produce visual stimuli for vision research
      experiments."""
)








