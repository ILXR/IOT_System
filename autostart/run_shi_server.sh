WORKON_HOME=~/virtualenv
ENV=shi
cd ~/Program/Fabric_pillow
source $WORKON_HOME/$ENV/bin/activate
python ~/Program/Fabric_pillow/main.py >& log
deactivate