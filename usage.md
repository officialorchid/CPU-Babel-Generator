# CPU Babel Generator - Usage Instructions

The CPU Babel Generator implements a Library of Babel for simplified x86-64-inspired CPU cores. It generates unique micro-x86-64 processor designs based on seeded pseudo-random parameters, following the plan outlined in `memo.md`. Each generated core varies in ISA parameters (registers, addressing modes) and microarchitecture (decoder type, pipeline depth, execution units, memory interface).

This tool supports:
- **Procedural Generation**: Create Verilog code for CPU cores using a seed as the "address" in the library.
- **Similarity Search**: Find cores matching conceptual descriptions (e.g., "cisc powerful fast_memory").
- **Verification**: Basic syntax checking and synthesis estimation using Yosys (Verilator simulation stub included).

## Prerequisites

- **Python 3.6+**: Required for the generation script.
- **Verilog Tools** (for verification):
  - [Yosys](https://yosyshq.net/yosys/): For syntax checking and synthesis.
  - [Verilator](https://www.veripool.org/verilator/) (optional): For simulation (stubbed in current version).
- **System**: Linux/macOS recommended (tested on Linux). Install dependencies via package manager:
  ```
  # Ubuntu/Debian
  sudo apt install yosys verilator python3
  
  # macOS (with Homebrew)
  brew install yosys verilator python3
  ```

No additional Python packages are required (uses standard library + hashlib, random, etc.).

## Installation

1. Clone or download the project files (`cpu_babel_generator.py`, `memo.md`).
2. Ensure prerequisites are installed.
3. Make the script executable (optional):
   ```
   chmod +x cpu_babel_generator.py
   ```

The project is self-contained; no setup.py or virtual environment needed.

## Basic Usage

Run the generator with a seed (required) and optional query words for search:

```
python3 cpu_babel_generator.py <seed> [query_words...]
```

- **`<seed>`**: A string seed (e.g., "seed_123", "library_position_42"). This determines the PRNG state and generates a unique CPU core. Seeds act as "addresses" in the infinite library.
- **`[query_words...]`**: Optional space-separated words from the lexicon (see Search section). Performs similarity search and prints matching seeds.

### Example: Generate a Single Core

```
python3 cpu_babel_generator.py seed_123
```

**Output**:
- Prints generated parameters (e.g., `{'num_regs': 6, 'decoder_type': 'microcoded', ...}`).
- Creates a Verilog file: `micro_x86_core_<hash>.v` in the current directory.
- Runs verification (syntax check, synthesis stats).
- Generates `assembler.py` (placeholder assembler).

The Verilog file contains:
- Register file module (parameterized by number of registers).
- Decoder (hardwired or microcoded).
- ALU/AGU (single or separate units).
- Memory interface (simple or cached).
- Top-level `micro_x86_core` module with pipeline stubs.

### Example: Generate and Verify

```
python3 cpu_babel_generator.py seed_456
```

If verification passes:
```
Syntax check passed.
Synthesis: [Yosys stats: gate count, etc.]
Core verified successfully.
Assembler generated: assembler.py
Generated Verilog: micro_x86_core_a1b2c3d4.v
```

If it fails (e.g., syntax error), it prints "Verification failed."

## Search Functionality (Phase 3)

The generator includes a similarity search using a lexicon of x86-64 concepts. Provide query words to find seeds generating "similar" cores.

### Lexicon

| Word            | Favored Parameters |
|-----------------|--------------------|
| `cisc`         | Microcoded decoder |
| `risc_like`    | Hardwired decoder |
| `compact`      | 4 registers, simple addressing ([reg]) |
| `powerful`     | 8 registers, full addressing ([reg], [reg+imm], [reg+reg]) |
| `fast_memory`  | Cached memory interface |
| `simple_memory`| Simple fixed-latency memory |
| `deep_pipeline`| 4-stage pipeline |
| `shallow_pipeline` | 2-stage pipeline |

### Example: Search for CISC-like Powerful Cores

```
python3 cpu_babel_generator.py seed_789 cisc powerful fast_memory
```

**Output**:
- Generates core for `seed_789`.
- Performs search over 10 example seeds.
- Prints top 5 matching seeds by "distance" (lower is better match):
  ```
  Search results: [('seed_2', 45.0), ('seed_5', 67.0), ...]
  ```

Use search to explore the library: Generate cores for matching seeds to get designs close to your conceptual query.

### Custom Search

Modify `similarity_search` in the script to use more seeds or advanced distance metrics (currently simple hash-based Euclidean).

## Generated Components

### ISA: micro-x86-64

- **Architecture**: 64-bit flat memory.
- **Registers**: 4/6/8 GPRs (mapped to RAX-R11).
- **Instructions** (fixed subset):
  - Arithmetic: ADD, SUB, AND, OR, XOR, INC, DEC.
  - Data: MOV (reg/reg/imm/mem).
  - Control: JMP, CMP, JE, JNE.
  - Stack: PUSH, POP.
- **Addressing Modes** (parameterized): [reg], [reg+imm8], [reg+reg].
- **Encoding**: Fixed 32-bit: [Opcode 8b | Dest 3b | Src1 3b | Mode 4b | Imm/Offset 14b].

### Microarchitecture Variations

- **Decoder**: Hardwired (simple) or microcoded (CISC-style with ROM).
- **Pipeline**: 2/3/4 stages (fetch/decode/execute/memory/writeback).
- **Execution**: Single ALU or separate AGU+ALU.
- **Memory**: Simple (1KB RAM) or cached (16-entry direct-mapped I-cache).

### Assembler

A placeholder `assembler.py` is generated. It needs expansion to parse micro-x86-64 assembly (e.g., `MOV RAX, 10`) into 32-bit binaries for simulation.

Example extension:
```python
def assemble(line):
    if 'MOV' in line:
        # Parse and encode
        return 0x...  # 32-bit instruction
    return 0xDEADBEEF  # Placeholder
```

## Verification (Phase 4)

- **Syntax Check**: Yosys reads and checks hierarchy.
- **Synthesis**: Estimates gate count with Yosys `synth` and `abc`.
- **Simulation**: Stubbed for Verilator. To enable:
  1. Write `test.cpp` with test program (sum array via assembled binary).
  2. Uncomment Verilator line in `verify_verilog`.
  3. Run: `make -f Vmicro_x86_core.mk` (generated by Verilator).

Failed generations (e.g., large designs) are discarded in production use.

## Advanced Usage

### Batch Generation

Script a loop to generate multiple cores:
```bash
for i in {1..100}; do
    python3 cpu_babel_generator.py "library_$i"
done
```

### Custom Parameters

Edit `MicroX86Params` class to add options (e.g., more instructions, pipeline stages).

### Extending the Lexicon

Add to `LEXICON` dict for new search concepts:
```python
'vectorized': {'exec_units': 'separate_agu_alu'}
```

### Troubleshooting

- **Yosys Not Found**: Install via package manager or build from source.
- **Verilog Syntax Errors**: Check generated `.v` file; incomplete instantiations are placeholders.
- **PRNG Determinism**: Same seed always produces same core (reproducible library).
- **Large Designs**: Increase filters in `verify_verilog` (e.g., gate count < 10000).
- **No Output Dir**: Files save to current working directory.

## Example Workflow

1. **Explore Concepts**: `python3 cpu_babel_generator.py seed_0 cisc deep_pipeline`
2. **Generate Specific Core**: `python3 cpu_babel_generator.py seed_2` (from search results).
3. **Verify & Simulate**:
   ```
   yosys -p "read_verilog micro_x86_core_*.v; synth; show"
   ```
4. **Assemble Test Program**: Extend `assembler.py` and run binary on simulator.

## Limitations & Next Steps

- **Assembler**: Placeholder; implement full parsing/encoding.
- **Simulation**: Add real test programs (e.g., array sum).
- **Search**: Basic distance; improve with vector embeddings.
- **Scale**: For full library, parallelize generation and store param metadata.
- **HDL**: Verilog only; add VHDL support.

See `memo.md` for architectural details and expansion ideas.

For issues, check console output or generated files. Contribute via pull requests!
