import os
import sys
import platform
from setuptools import setup, Extension
import pybind11

# Determine if we're on Windows (for specific MSVC/MinGW flags)
is_windows = platform.system() == "Windows"

# Setup CMake arguments
def get_cmake_args():
    cmake_args = [
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_VERBOSE_MAKEFILE=ON",
        "-DPYTHON_EXECUTABLE={}".format(sys.executable),
    ]

    # On Windows, you can specify compiler flags here if necessary
    if is_windows:
        cmake_args.append("-GVisual Studio 16 2019")  # or another Visual Studio version, depending on your setup
    
    return cmake_args

# Define a function that builds the extension
def build_extension():
    cmake_args = get_cmake_args()
    build_args = ["--config", "Release"]

    # Check the platform and set specific flags
    if is_windows:
        # You can modify the flags here if you need specific handling for MSVC or MinGW
        pass

    # Run CMake commands to build the extension
    from setuptools.command.build_ext import build_ext
    class build_ext_cmake(build_ext):
        def run(self):
            # Run CMake to configure and build the project
            self.build_temp = os.path.join(self.build_lib, "temp")
            cmake_args.append(f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={self.build_lib}")
            build_ext.run(self)

    return build_ext_cmake

# Define the C++ extension using pybind11
ext_modules = [
    Extension(
        name="mylib",
        sources=["main.cpp"],  # Path to your C++ source file
        include_dirs=[pybind11.get_include()],
        language="c++",
    )
]

# Setup function
setup(
    name="mylib",
    version="0.1",
    description="My C++ extension for Python",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_extension()},
)
