cd /home/hw1020/Downloads/Installed_Package/verilator
sudo make uninstall
git checkout -v
autoconf
./configure
make -j `nproc`
sudo make install