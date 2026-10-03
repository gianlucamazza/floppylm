// Demonstrates the current classification with no GPU call or in-flight work.
#include "gpu_wait.h"
#include <iostream>

int main() {
  PublishedFenceWatch watch;
  GpuRuntimeFault fault;
  if (watch.observe({true, 113834, 0}, 600000, fault))
    return 1;
  if (!watch.observe({true, 113834, 600806}, 600000, fault))
    return 1;
  std::cout << "{\"gpu_calls_executed\":0,\"job_active\":true,"
               "\"fence_unchanged\":true,\"fault_kind\":\""
            << fault.kind << "\",\"requested_fence\":" << fault.requested_fence
            << ",\"elapsed_ms\":" << fault.elapsed_ms << "}\n";
}
