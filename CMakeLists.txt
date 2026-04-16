cmake_minimum_required(VERSION 3.8)
project(AZ_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)  # ADD THIS

# --- C++ executable (unchanged) ---
add_executable(execute_prerecorded src/execute_prerecorded.cpp)
target_include_directories(execute_prerecorded PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>)
target_compile_features(execute_prerecorded PUBLIC c_std_99 cxx_std_17)
install(TARGETS execute_prerecorded
  DESTINATION lib/${PROJECT_NAME})

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS src/get_joints.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME get_joints)

install(PROGRAMS src/execute_trajectory.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME execute_trajectory)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()