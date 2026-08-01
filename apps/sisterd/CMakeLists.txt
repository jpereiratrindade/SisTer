find_package(OpenSSL REQUIRED)
find_package(PostgreSQL)

add_executable(
    sisterd
    main.cpp
    auth.cpp
    db.cpp
    studio_client.cpp
    sister_campo_client.cpp
    api/maturity_routes.cpp
    http/content_length.cpp
    identity/internal_assertion.cpp
    integrations/nexo_client.cpp
    runtime/connection_thread_pool.cpp
    security/login_rate_limiter.cpp
)

if(PostgreSQL_FOUND)
    target_compile_definitions(sisterd PRIVATE SISTER_HAVE_LIBPQ=1)
    target_link_libraries(sisterd PRIVATE sister_core OpenSSL::SSL OpenSSL::Crypto PostgreSQL::PostgreSQL)
else()
    message(STATUS "libpq not found — sisterd will run without PostgreSQL support")
    target_link_libraries(sisterd PRIVATE sister_core OpenSSL::SSL OpenSSL::Crypto)
endif()

target_compile_features(sisterd PRIVATE cxx_std_20)
target_compile_definitions(sisterd PRIVATE SISTER_VERSION="${PROJECT_VERSION}")

if(MSVC)
    target_compile_options(sisterd PRIVATE /W4)
else()
    target_compile_options(sisterd PRIVATE -Wall -Wextra -Wpedantic)
endif()
