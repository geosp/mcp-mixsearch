# Manual checks

This project has no verifier agent, so a phase whose behavior needs real input ends with a **manual check**. The check is recorded here, one folder per check: `docs/demos/<YYYY-MM-DD>-<slug>/README.md`. It may come with small scripts that generate inputs or compare outputs.

Each record states:

- **Result:** pass or fail, in one line.
- **Machine:** CPU, GPU (if any) and OS.
- **Versions:** the commit checked and the relevant dependency versions.
- **Who ran it:** the owner, or an agent the owner delegated to.
- **Commands:** what was run, exactly, and the input used. Describe the input when it is data the project keeps out of Git; never copy that data here.
- **Observations:** what happened, with numbers where they exist.

The PR that closes the phase links its record.
