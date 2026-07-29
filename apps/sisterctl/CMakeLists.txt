find_package(OpenSSL REQUIRED)

add_executable(sisterctl main.cpp ../sisterd/auth.cpp)
target_include_directories(sisterctl PRIVATE ../sisterd)
target_link_libraries(sisterctl PRIVATE sister_core OpenSSL::Crypto)
target_compile_features(sisterctl PRIVATE cxx_std_20)
