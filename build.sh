cd judger
rm -rf build && mkdir build && cd build && cmake ..
make || exit 1
make install
cd ../bindings/Python && rm -rf build && python setup.py install || exit 1
