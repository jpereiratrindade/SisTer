cmake_minimum_required(VERSION 3.20)

file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" SISTER_VERSION LIMIT_COUNT 1)
if(NOT SISTER_VERSION MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
    message(FATAL_ERROR "VERSION must contain a semantic version such as 0.2.3")
endif()

project(SisTer
    VERSION "${SISTER_VERSION}"
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
