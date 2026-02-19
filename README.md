# NVCF Container Helpers
This repository contains examples, tests, and a library to ensure a smooth deployment within 
[NVIDIA Cloud Functions (NVCF)](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html).

## NVCF Container Helper Functions Library
The package `nvcf_container` provide Python functions that simplify common tasks within containers deployed inside  
[NVIDIA Cloud Functions](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html)

## Container Examples
The [examples/](./examples) folder has sample containers to be built and used as functions or tasks.

## Agent Skills
This repository includes reusable agent skills in [skills/](./skills). The format is based on the open Agent Skills specification:
[https://agentskills.io/home](https://agentskills.io/home).

- [NGC Cloud Functions CLI Skill](./skills/nvcf-ngc-cli-skill/SKILL.md): Guidance for using NGC CLI with NVCF functions, tasks, clusters, GPUs, and the NGC registry as well as invoking functions and debugging deployment errors.
- Additional workflows are in [examples.md](./skills/nvcf-ngc-cli-skill/examples.md).

### Add this skill to Claude
Create a local skills directory for Claude and copy this skill into it:

```bash
mkdir -p ~/.claude/skills
cp -R ./skills/nvcf-ngc-cli-skill ~/.claude/skills/
```

### Add this skill to Cursor
Create a local skills directory for Cursor and copy this skill into it:

```bash
mkdir -p ~/.cursor/skills
cp -R ./skills/nvcf-ngc-cli-skill ~/.cursor/skills/
```
