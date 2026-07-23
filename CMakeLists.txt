cmake_minimum_required(VERSION 3.20)

project(SisTer
    VERSION 0.2.1
    DESCRIPTION "SisTer federative territorial convergence platform prototype"
    LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(SISTER_BUILD_TESTS "Build SisTer tests" ON)

add_subdirectory(core)
add_subdirectory(apps/sisterctl)
add_subdirectory(apps/sisterd)

if(SISTER_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
