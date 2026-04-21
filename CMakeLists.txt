cmake_minimum_required(VERSION 3.8)
project(AZ_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS src/get_joints.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME get_joints)

install(PROGRAMS src/execute_trajectory.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME execute_trajectory)

install(PROGRAMS src/trajectory_gui.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME trajectory_gui)

install(PROGRAMS src/joy_teleop.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME joy_teleop)

install(PROGRAMS src/cartesian_admittance.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cartesian_admittance)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)
  
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