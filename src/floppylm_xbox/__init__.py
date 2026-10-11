"""Xbox Series S execution for FloppyLM E0 (ADR 0009, ADR 0012).

Job preparation and numerical gates (`jobs`), the per-operation oracle (`kernels`),
the Device Portal transport (`portal`), and host invocation of the xbox-gpu-training
console lifecycle tool (`console_lifecycle`). The core `floppylm` package never
imports this one.
"""
