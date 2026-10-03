// Offline validation only: no kernels, training, reconciliation or Xbox writes.
#include "model.h"
#include <iostream>

int main(int argc, char **argv) {
  if (argc != 6)
    return 2;
  try {
    auto job = e0::read_json(argv[1]);
    const auto initial = e0::read_json(argv[2]);
    const auto checkpoint = e0::read_json(argv[3]);
    job["tensors"] = initial.at("tensors");
    job["initialization_sha256"] = job.at("initialization").at("sha256");
    e0::Model model(job);
    uint64_t step = 0;
    model.restore(checkpoint, job, step);
    if (model.checkpoint(step, job) != checkpoint)
      throw std::runtime_error("restore roundtrip differs");
    e0::Model first(e0::read_json(argv[4]));
    e0::Model second(e0::read_json(argv[5]));
    auto rejects = [&](e0::Json changed) {
      try {
        model.restore(changed, job, step);
      } catch (const std::exception &) {
        return true;
      }
      return false;
    };
    auto bad_stream = checkpoint;
    bad_stream["stream_position"] = 0;
    auto bad_moment = checkpoint;
    bad_moment["moments"][0]["second"][0] = -1.0;
    auto bad_recipe = checkpoint;
    bad_recipe["spec"]["seed"] = 999;
    const bool stream = rejects(bad_stream), moment = rejects(bad_moment),
               recipe = rejects(bad_recipe);
    if (!stream || !moment || !recipe)
      throw std::runtime_error("mutation was accepted");
    std::cout << e0::Json{{"ok", true},
                          {"checkpoint_step", checkpoint.at("step")},
                          {"stream_position", checkpoint.at("stream_position")},
                          {"tensor_count", model.parameters.size()},
                          {"exact_restore_roundtrip", true},
                          {"branch_models_valid", 2},
                          {"rejects_stream_mutation", stream},
                          {"rejects_negative_second_moment", moment},
                          {"rejects_recipe_mutation", recipe},
                          {"training_executed", false}}
                     .dump(2)
              << '\n';
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
