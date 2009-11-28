#!/bin/sh

# 28-11-09
# By using ths download script, an assumption is made that
# you have done a full slackware 13.0 install

# These scripts require arch to be modified (x86 or x86_64)
# zum Beispiel: sh ARCH=x86_64 asdf.SlackBuild

$(which wget) -c -nd -nH \
  http://slackbuilds.org/slackbuilds/13.0/libraries/wxGTK.tar.gz \
  http://downloads.sourceforge.net/wxwindows/wxGTK-2.8.9.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/wxPython.tar.gz \
  http://downloads.sourceforge.net/wxpython/wxPython-src-2.8.10.1.tar.bz2 \
  http://slackbuilds.org/slackbuilds/13.0/development/PyOpenGL.tar.gz \
  http://downloads.sourceforge.net/pyopengl/PyOpenGL-3.0.0a5.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/python-xlib.tar.gz \
  http://downloads.sourceforge.net/python-xlib/python-xlib-0.14.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/development/numpy.tar.gz \
  http://downloads.sourceforge.net/numpy/numpy-1.3.0.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/pyusb.tar.gz \
  http://downloads.sourceforge.net/pyusb/pyusb-0.4.1.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/academic/scipy.tar.gz \
  http://downloads.sourceforge.net/scipy/scipy-0.7.0.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/fftw.tar.gz \
  ftp://ftp.fftw.org/pub/fftw/fftw-3.2.1.tar.gz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/blas.tar.gz \
  http://www.netlib.org/blas/blas.tgz \
  http://slackbuilds.org/slackbuilds/13.0/libraries/lapack.tar.gz.asc \
  http://www.netlib.org/lapack/lapack.tgz

# These scripts require some minor modification, like version number etc.
wget -c -nd -nH \
  http://slackbuilds.org/slackbuilds/12.2/development/swig.tar.gz \
  http://downloads.sourceforge.net/swig/swig-1.3.40.tar.gz
