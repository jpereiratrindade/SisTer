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

find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME sisterctl_bootstrap_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterctl_bootstrap_test.py
        $<TARGET_FILE:sisterctl>)

add_test(
    NAME sisterd_clima_proxy_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_clima_proxy_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_transport_quarantine_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_transport_quarantine_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_systemd_unit_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_systemd_unit_test.py
        ${CMAKE_SOURCE_DIR}/ops/systemd/sisterd.service)

add_test(
    NAME sisterd_maturity_api_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_maturity_api_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web
        ${CMAKE_SOURCE_DIR})

add_test(
    NAME sister_maturity_contract_tests
    COMMAND
        ${Python3_EXECUTABLE} -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/maturity
        -p test_*.py)
