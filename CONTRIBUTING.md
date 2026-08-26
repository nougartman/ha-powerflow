# Contributing to Powerflow

Contributions are welcome! Please read the guidelines below before opening a PR.

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/nougartman/ha-powerflow.git
cd ha-powerflow

# Install test dependencies
pip install pytest pytest-homeassistant-custom-component pytest-asyncio aiohttp

# Run the test suite
pytest tests/ -v --tb=short
```

---

## Code Style

- All Python must use `async`/`await` throughout — no blocking calls on the event loop
- Add `from __future__ import annotations` at the top of every Python file
- Follow [Home Assistant development guidelines](https://developers.home-assistant.io/)
- Target HA core >= 2024.1

---

## How to Contribute

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feat/my-feature`)
3. Write code with appropriate tests in `tests/`
4. Open a **Pull Request** targeting `main`
5. CI will automatically run HASSfest validation, HACS validation, and the pytest suite

---

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a clear description of what changed and why
- All new engine logic should have corresponding unit tests
- Do not modify `hacs.json` or `manifest.json` version fields manually — releases handle this

---

## Reporting Issues

Please open a [GitHub Issue](https://github.com/nougartman/ha-powerflow/issues) with:
- Your HA version
- Powerflow version
- Relevant logs from **Settings → System → Logs** filtered by `powerflow`
- Steps to reproduce the problem

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
