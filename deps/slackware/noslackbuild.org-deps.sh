#!/bin/sh

# TODO
# - make slackbuild that installs this thing
# - make slackbuild that also builds the python bindings

# These files require a slackbuild file to build
$(which wget) -c -nd -nH \
  http://downloads.sourceforge.net/project/mdp-toolkit/mdp-toolkit/2.5/MDP-2.5.tar.gz?use_mirror=switch \
  http://prdownloads.sourceforge.net/fann/fann-2.0.0.tar.bz2?download

$(which mv) MDP-*.tar.gz mdp/
$(which mv) fann-*.tar.bz2 fann/
