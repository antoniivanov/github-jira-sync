
if ! which python3 >/dev/null 2>&1 ; then
  echo "ERROR:"
  echo "Please install python 3.9+. Build cannot continue without it."
  echo "If you are new to python:"
  echo "There are some awesome tools for installing and managing python which we recommend:"
  echo " - conda - https://conda.io/projects/conda/en/latest/user-guide/getting-started.html"
  echo " - pyenv - https://github.com/pyenv/pyenv"
  echo "      - If you use pyenv we also recommend https://github.com/pyenv/pyenv-virtualenv"
  echo ""
  exit 1
fi

cd "$(dirname $0)" || exit 1
cd ..


echo "Update pip to newest version"
pip install -U pip

echo "Install in editable mode (develop mode)"
pip install -e .

echo "install dependencies from requirements.txt (used for development and testing)"
pip install  -r requirements.txt

pytest --junitxml=tests.xml --cov issues_sync --cov-report term-missing --cov-report xml:coverage.xml

python setup.py sdist --formats=gztar
