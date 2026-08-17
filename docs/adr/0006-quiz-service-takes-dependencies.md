# The quiz service takes dependencies, unlike classroom

`msu/classroom` states in its `pyproject.toml` that it has no dependencies at all — the course description is plain Python, the ledger is `sqlite3`, HTTP is `urllib`, and the payoff is that a teaching machine needs nothing beyond the system interpreter. The quiz service is the sibling of that service, deployed by the same Ansible on the same host, and it deliberately does not follow the rule.

It uses FastAPI for the HTTP layer, `qrcode` for the tickets and `reportlab` for the handout PDF, in a virtualenv managed by its role.

The rule was worth breaking because the two services meet the outside world differently. `classroom` answers webhooks from Gitea: a handful of POSTs a day from one client that retries. The quiz service is opened by thirty-six phones at once, on lecture-hall wifi, with a two-minute clock running — and it has to render a printable sheet of QR codes. Hand-rolling that on `http.server` means writing a QR encoder and a PDF writer, several hundred lines whose only purpose is to avoid `pip install`, and which nobody will ever revisit or test seriously. Those two libraries are old, boring, and exactly the kind of thing a virtualenv exists for.

The dependency is also contained. It lives on the server, behind the same nginx proxy as everything else; it does not reach the students' machines, so the promise `classroom` actually cares about — that a teaching machine needs only `python3` — is untouched. The cost is a virtualenv on `elysium` that the role has to build and keep current, and one more thing that can fail at deploy time rather than at runtime.

If the service ever has to run somewhere without network access to an index, this is the decision to revisit; pinning the three packages into the repo would be the cheaper move then, not rewriting the QR encoder.
