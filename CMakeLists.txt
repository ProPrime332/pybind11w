cmake_minimum_required(VERSION 3.12)
project(main)

set(CMAKE_CXX_STANDARD 11)
find_package(pybind11 REQUIRED)

pybind11_add_module(main.cpp)

