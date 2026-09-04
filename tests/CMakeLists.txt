add_executable(sister_core_tests core_tests.cpp)
target_link_libraries(sister_core_tests PRIVATE sister_core)
target_compile_features(sister_core_tests PRIVATE cxx_std_20)

add_test(NAME sister_core_tests COMMAND sister_core_tests)

find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

add_executable(
    sisterd_auth_tests
    auth_tests.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/auth.cpp)
target_include_directories(sisterd_auth_tests PRIVATE ${CMAKE_SOURCE_DIR}/apps/sisterd)
target_link_libraries(sisterd_auth_tests PRIVATE OpenSSL::Crypto)
target_compile_features(sisterd_auth_tests PRIVATE cxx_std_20)

add_test(NAME sisterd_auth_tests COMMAND sisterd_auth_tests)

add_executable(
    sisterd_internal_assertion_tests
    internal_assertion_tests.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/identity/internal_assertion.cpp)
target_include_directories(
    sisterd_internal_assertion_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/apps/sisterd/identity)
target_link_libraries(sisterd_internal_assertion_tests PRIVATE OpenSSL::Crypto)
target_compile_features(sisterd_internal_assertion_tests PRIVATE cxx_std_20)

add_test(NAME sisterd_internal_assertion_tests COMMAND sisterd_internal_assertion_tests)

add_executable(
    sisterd_security_hardening_tests
    security_hardening_tests.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/http/content_length.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/runtime/connection_thread_pool.cpp
    ${CMAKE_SOURCE_DIR}/apps/sisterd/security/login_rate_limiter.cpp)
target_include_directories(
    sisterd_security_hardening_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/apps/sisterd/http
    ${CMAKE_SOURCE_DIR}/apps/sisterd/runtime
    ${CMAKE_SOURCE_DIR}/apps/sisterd/security)
target_link_libraries(sisterd_security_hardening_tests PRIVATE Threads::Threads)
target_compile_features(sisterd_security_hardening_tests PRIVATE cxx_std_20)

add_test(NAME sisterd_security_hardening_tests COMMAND sisterd_security_hardening_tests)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME participation_contract_tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/participation_contract_test.py)

add_test(
    NAME arc01_contract_tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/arc01_contract_test.py)

add_test(
    NAME component_runtime_contract_tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/component_runtime_contract_test.py)


add_test(
    NAME participation_persistence_tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/participation_persistence_test.py)

add_test(
    NAME participation_assessment_tests
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/participation_assessment_test.py)
add_test(
    NAME gateway_security_profile_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/gateway_security_profile_test.py)

add_test(
    NAME gateway_config_render_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/gateway_config_render_test.py)

add_test(
    NAME gateway_candidate_config_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/gateway_candidate_config_test.py)

add_test(
    NAME sec03v_env_preflight_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sec03v_env_preflight_test.py)

add_test(
    NAME haproxy_packaging_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/haproxy_packaging_test.py)

foreach(gateway_test IN ITEMS
        gateway_protocol_test.py
        gateway_header_sanitization_test.py
        gateway_failure_test.py
        gateway_abuse_test.py
        gateway_slow_client_test.py
        gateway_upstream_resilience_test.py)
    get_filename_component(gateway_test_name ${gateway_test} NAME_WE)
    add_test(
        NAME ${gateway_test_name}s
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/${gateway_test})
    set_tests_properties(${gateway_test_name}s PROPERTIES SKIP_RETURN_CODE 77)
endforeach()

add_test(
    NAME gateway_lab_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/gateway_lab_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)
set_tests_properties(gateway_lab_tests PROPERTIES SKIP_RETURN_CODE 77)

add_test(
    NAME sisterctl_bootstrap_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterctl_bootstrap_test.py
        $<TARGET_FILE:sisterctl>)

add_test(
    NAME sisterd_reference_integration_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_reference_integration_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME reference_subsystem_contract_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/reference_subsystem_contract_test.py)

add_test(
    NAME sisterd_transport_quarantine_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_transport_quarantine_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_http_hardening_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_http_hardening_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_systemd_unit_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_systemd_unit_test.py
        ${CMAKE_SOURCE_DIR}/ops/systemd/sisterd.service
        ${CMAKE_SOURCE_DIR}/ops/systemd/sisterd.socket
        ${CMAKE_SOURCE_DIR}/ops/tmpfiles.d/sister.conf)

add_test(
    NAME sister_gateway_systemd_unit_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sister_gateway_systemd_unit_test.py
        ${CMAKE_SOURCE_DIR}/ops/systemd/sister-gateway.service)

add_test(
    NAME sisterd_unix_listener_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_unix_listener_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_maturity_api_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_maturity_api_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web
        ${CMAKE_SOURCE_DIR})

add_test(
    NAME sisterd_system_catalog_health_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_system_catalog_health_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME sisterd_ecosystem_api_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/sisterd_ecosystem_api_test.py
        $<TARGET_FILE:sisterd>
        ${CMAKE_SOURCE_DIR}/web)

add_test(
    NAME ecosystem_projection_renderer_tests
    COMMAND
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/ecosystem_projection_renderer_test.py)

add_test(
    NAME sister_maturity_contract_tests
    COMMAND
        ${Python3_EXECUTABLE} -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/maturity
        -p test_*.py)
