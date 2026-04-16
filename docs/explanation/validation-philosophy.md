# Validation philosophy

This project does not depend on bundled MATLAB reference files. Instead, it validates correctness through multiple complementary layers.

The detailed validation page remains here:

- [Validation strategy](../validation.md)

## Why use multiple layers

A single golden reference file is fragile. It can confirm that one output matches one previous output, but it does not by itself establish that the implementation is physically or mathematically trustworthy.

The current project therefore combines:

- source-faithful algorithm design
- analytical validation with Taylor–Green vortex
- physical consistency checks such as the energy identity
- manuscript-style qualitative checks
- CPU↔GPU agreement

## Why this matters

This approach is a better fit for:

- an independent Python port
- a repo that should remain lightweight and redistributable
- future backend work where agreement and physical behavior matter as much as one exact file match
