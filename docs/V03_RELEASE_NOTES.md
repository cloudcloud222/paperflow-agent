# Paper-Agent V0.3 Release Notes

V0.3 focuses on two things:

1. **Safety boundary for CLI runs**: quick tests and full paper generation are now separated.
2. **A lightweight Web UI**: users can create a project, upload materials, configure model settings, run quick tests, generate outline or limited nodes, and download outputs.

## Key changes

### Safer CLI

`run` no longer starts the full workflow by default.

```bash
python paper_agent.py run --project examples/demo_project
```

The command above only prints a safety message. Users must select a mode explicitly:

```bash
python paper_agent.py run --project examples/demo_project --mode quick
python paper_agent.py run --project examples/demo_project --mode literature
python paper_agent.py run --project examples/demo_project --mode outline
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1 --no-polish --no-review --no-revision
python paper_agent.py run --project examples/demo_project --mode full --full --yes
```

### Limited node test

`node` mode defaults to a small number of nodes. It supports:

- `--max-nodes`
- `--no-polish`
- `--no-review`
- `--no-revision`
- `--assemble`

This makes debugging much cheaper and faster than running the whole paper pipeline.

### Web UI

Start the web interface:

```bash
python paper_agent.py web --host 127.0.0.1 --port 8501
```

The Web UI supports:

- create/edit project topic and goal;
- upload PDF/DOCX/TXT materials;
- configure provider, model, base URL and proxy;
- run Check, Ping, QuickTest, Outline, Node Test and Full Run;
- inspect outputs and download an outputs zip.

Design style: light blue, light gray and white, with rounded cards/buttons inspired by Microsoft/Google web interfaces.

## Recommended demo flow

```bash
python paper_agent.py check --project examples/demo_project
python paper_agent.py ping --project examples/demo_project
python paper_agent.py quicktest --project examples/demo_project --max-chars 800
python paper_agent.py run --project examples/demo_project --mode outline
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1 --no-polish --no-review --no-revision
```

Only use full mode when needed:

```bash
python paper_agent.py run --project examples/demo_project --mode full --full --yes
```
