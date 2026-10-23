#!/usr/bin/env bash
# Builds this episode's example in <dir> (default: submodule-example):
#
#   <dir>/upstream/lib.git  the library, 30 commits
#   <dir>/monorepo/         an app, 40 commits, and the library as a submodule at vendor/lib
#   <dir>/gitconfig         your Git config, plus what reaches the library
#
# It's the setup the git-splice chapter tests with, so the commits and
# their hashes are the ones in the episode. Then try the episode's
# commands in <dir>/monorepo.
set -euo pipefail

episode=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
dir=${1:-submodule-example}
if [[ -e $dir ]]; then
  echo "$dir exists already" >&2
  exit 1
fi
mkdir -p "$dir"
cd "$dir"
root=$(pwd)

# Builds upstream/lib.git and monorepo/, and changes into monorepo/.
# shellcheck source=../git-splice/test/comparisons/scrut-setup.sh
source "$episode/../git-splice/test/comparisons/scrut-setup.sh"
unset -f git
rm -rf ../splice-monorepo

git submodule add -q https://git.example.com/lib.git vendor/lib
git commit -q -m "add lib as a submodule"

# The library's URL is a stand-in, https://git.example.com/lib.git, as in
# the episode. This config makes Git find it in upstream/lib.git, after
# your own config, and allows the local clone a submodule needs.
cat >"$root/gitconfig" <<CONFIG
[include]
	path = ~/.gitconfig
	path = ~/.config/git/config
[url "$root/upstream/"]
	insteadOf = https://git.example.com/
[protocol "file"]
	allow = always
CONFIG

cat <<MESSAGE
Built $root. To try the episode's commands, use its gitconfig:

  export GIT_CONFIG_GLOBAL=$root/gitconfig   # fish: set -x GIT_CONFIG_GLOBAL $root/gitconfig
  cd $root/monorepo
  git ls-tree HEAD vendor/lib
MESSAGE
