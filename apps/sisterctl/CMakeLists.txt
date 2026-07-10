add_executable(sisterctl main.cpp)
target_link_libraries(sisterctl PRIVATE sister_core)
target_compile_features(sisterctl PRIVATE cxx_std_20)
