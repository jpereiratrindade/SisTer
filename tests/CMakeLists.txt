add_executable(sister_core_tests core_tests.cpp)
target_link_libraries(sister_core_tests PRIVATE sister_core)
target_compile_features(sister_core_tests PRIVATE cxx_std_20)

add_test(NAME sister_core_tests COMMAND sister_core_tests)

find_package(OpenSSL REQUIRED)

add_executable(
    sisterd_auth_tests
    auth_tests.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/auth.cpp)
target_include_directories(sisterd_auth_tests PRIVATE ${CMAKE_SOURCE_DIR}/apps/sisterd)
target_link_libraries(sisterd_auth_tests PRIVATE OpenSSL::Crypto)
target_compile_features(sisterd_auth_tests PRIVATE cxx_std_20)

add_test(NAME sisterd_auth_tests COMMAND sisterd_auth_tests)
