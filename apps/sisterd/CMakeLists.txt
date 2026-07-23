find_package(OpenSSL REQUIRED)

add_executable(sisterd main.cpp auth.cpp)
target_link_libraries(sisterd PRIVATE sister_core OpenSSL::Crypto)
target_compile_features(sisterd PRIVATE cxx_std_20)

if(MSVC)
    target_compile_options(sisterd PRIVATE /W4)
else()
    target_compile_options(sisterd PRIVATE -Wall -Wextra -Wpedantic)
endif()
