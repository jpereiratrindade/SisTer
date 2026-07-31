cmake_minimum_required(VERSION 3.20)
project(SisTerLab LANGUAGES CXX)

# O Lab não recompõe nem reimplementa os alvos.
# Ele agrega exatamente os snapshots registrados.
add_subdirectory(target/sisterd)
add_subdirectory(target/sisterctl)
