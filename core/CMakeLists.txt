add_library(sister_core
    src/contract.cpp
    src/registry.cpp
    src/provenance.cpp
)

target_include_directories(sister_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(sister_core PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(sister_core PRIVATE /W4)
else()
    target_compile_options(sister_core PRIVATE -Wall -Wextra -Wpedantic)
endif()
