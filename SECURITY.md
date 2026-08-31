# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's **Report a vulnerability** facility in the
repository Security tab. Do not open a public issue for leaked data, validator bypasses, workflow
permission problems, or artifact-integrity failures.

Include the affected revision, a minimal reproduction without real secrets or prompt content, and
the impact you believe is possible. Maintainers will acknowledge the report and coordinate disclosure
after a fix is available.

## Scope

Security-sensitive boundaries include:

- acceptance of unknown or content-bearing contribution fields;
- secrets, identifiers, URLs, paths, or event-level data surviving validation;
- modification or replacement of accepted evidence;
- untrusted pull-request code executing with write permissions;
- revoked bundles appearing in compiled totals;
- nondeterministic or incorrectly checksummed release artifacts.

Only the latest revision on `main` is supported while the project remains pre-release.
