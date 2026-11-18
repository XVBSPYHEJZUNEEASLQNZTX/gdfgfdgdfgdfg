if ( NOT ANDROID_ABI OR NOT CMAKE_BUILD_TYPE )
    return()
endif()

if(${ANDROID_ABI} STREQUAL "x86_64")
    set(_conan_arch "x86_64")
elseif(${ANDROID_ABI} STREQUAL "x86")
    set(_conan_arch "x86")
elseif(${ANDROID_ABI} STREQUAL "arm64-v8a")
    set(_conan_arch "armv8")
elseif(${ANDROID_ABI} STREQUAL "armeabi-v7a")
    set(_conan_arch "armv7")
else()
    message(FATAL_ERROR "Not supported configuration: ${ANDROID_ABI}")
endif()

# Use the conan toolchain generated for the requested build type. If conan was run only for
# some build types (see -PfptnConanBuildTypes in app/build.gradle.kts), fall back to one that
# exists, so the build does not depend on which type the Android Gradle Plugin asks for.
set(_conan_tc_found FALSE)
foreach(_bt IN ITEMS "${CMAKE_BUILD_TYPE}" RelWithDebInfo Release Debug)
    set(_conan_tc "${CMAKE_CURRENT_LIST_DIR}/build/${_conan_arch}/${_bt}/generators/conan_toolchain.cmake")
    if(EXISTS "${_conan_tc}")
        include("${_conan_tc}")
        set(_conan_tc_found TRUE)
        break()
    endif()
endforeach()

if(NOT _conan_tc_found)
    message(FATAL_ERROR "conan toolchain not found for ${_conan_arch} (build type ${CMAKE_BUILD_TYPE}). Did 'conan install' run?")
endif()
