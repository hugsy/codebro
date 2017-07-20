# -*- mode: ruby -*-

$script = <<EOF
apt-get update
apt-get install -y pkg-config python python-dev build-essential python-wheel llvm-3.6-dev python-setuptools python-pip clang-3.6 python-clang-3.6 graphviz libgraphviz-dev --no-install-recommends
pip install --upgrade pip
pip uninstall pydot
apt-get install -y python-pydot
rm -fr -- /opt/codebro
git clone https://github.com/hugsy/codebro.git /opt/codebro
cd /opt/codebro
python -m pip install -r requirements.txt
cd codebro
python manage.py syncdb

cat >/etc/rc.local <<FOO
cd /opt/codebro/codebro
python manage.py runserver 0.0.0.0:8000 &
FOO

/etc/rc.local
echo "Successfully deployed !!"
EOF


Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.box_check_update = false
  config.vm.network "forwarded_port", guest: 8000, host: 8000, auto_correct: true
  config.vm.provision "shell", inline: $script
  config.vm.hostname = "codebro"

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024"]
    vb.customize ["modifyvm", :id, "--vram", "16"]
    vb.customize ["modifyvm", :id, "--cpus", "1"]
  end

end
