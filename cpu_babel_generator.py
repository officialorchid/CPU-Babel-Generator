#!/usr/bin/env python3
"""
CPU Babel Generator: Library of Babel for micro-x86-64 CPU cores.
Generates Verilog for simplified x86-64-inspired cores based on seeded PRNG parameters.
Supports phases: generation, search, verification.
"""

import random
import hashlib
import os
import subprocess
import sys
from typing import Dict, List, Tuple, Any

class MicroX86Params:
    """Parameters for micro-x86-64 ISA and microarchitecture."""
    
    # ISA Parameters
    NUM_REGS_OPTIONS = [4, 6, 8]
    REG_NAMES = ['RAX', 'RBX', 'RCX', 'RDX', 'R8', 'R9', 'R10', 'R11']  # First 8 for mapping
    
    INSTRUCTIONS = [
        'ADD', 'SUB', 'AND', 'OR', 'XOR', 'INC', 'DEC',
        'MOV', 'JMP', 'CMP', 'JE', 'JNE', 'PUSH', 'POP'
    ]
    
    ADDRESSING_MODES = [1, 2, 3]  # 1: [reg], 2: [reg+imm], 3: [reg+reg]
    
    # Microarchitecture Parameters
    DECODER_TYPES = ['hardwired', 'microcoded']
    PIPELINE_DEPTHS = [2, 3, 4]
    EXEC_UNITS = ['single_alu', 'separate_agu_alu']
    MEMORY_TYPES = ['simple', 'cached']  # cached: small I-cache
    
    # Lexicon for search
    LEXICON = {
        'cisc': {'decoder': 'microcoded'},
        'risc_like': {'decoder': 'hardwired'},
        'compact': {'num_regs': 4, 'addressing_modes': [1]},
        'powerful': {'num_regs': 8, 'addressing_modes': [1,2,3]},
        'fast_memory': {'memory': 'cached'},
        'simple_memory': {'memory': 'simple'},
        'deep_pipeline': {'pipeline_depth': 4},
        'shallow_pipeline': {'pipeline_depth': 2}
    }

def seed_to_params(seed: str) -> Dict[str, Any]:
    """Convert seed to parameters using PRNG."""
    random.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16))
    
    params = {
        'num_regs': random.choice(MicroX86Params.NUM_REGS_OPTIONS),
        'addressing_modes': random.sample(MicroX86Params.ADDRESSING_MODES, 
                                        k=random.randint(1, len(MicroX86Params.ADDRESSING_MODES))),
        'decoder_type': random.choice(MicroX86Params.DECODER_TYPES),
        'pipeline_depth': random.choice(MicroX86Params.PIPELINE_DEPTHS),
        'exec_units': random.choice(MicroX86Params.EXEC_UNITS),
        'memory_type': random.choice(MicroX86Params.MEMORY_TYPES),
        'instructions': MicroX86Params.INSTRUCTIONS  # Fixed for now
    }
    return params

def generate_register_file_verilog(params: Dict[str, Any]) -> str:
    """Generate Verilog for register file."""
    num_regs = params['num_regs']
    reg_width = 64
    template = f"""
module reg_file #(
    parameter NUM_REGS = {num_regs},
    parameter REG_WIDTH = {reg_width}
)(
    input clk,
    input we,  // write enable
    input [${{NUM_REGS-1}}:0] waddr,  // write address
    input [${{NUM_REGS-1}}:0] raddr1, raddr2,
    input [REG_WIDTH-1:0] wdata,
    output [REG_WIDTH-1:0] rdata1, rdata2
);
    reg [REG_WIDTH-1:0] regs [0:NUM_REGS-1];
    
    integer i;
    initial begin
        for (i = 0; i < NUM_REGS; i = i + 1) begin
            regs[i] = 64'h0;
        end
    end
    
    always @(posedge clk) begin
        if (we) begin
            regs[waddr] <= wdata;
        end
    end
    
    assign rdata1 = regs[raddr1];
    assign rdata2 = regs[raddr2];
endmodule
"""
    return template

def generate_decoder_verilog(params: Dict[str, Any]) -> str:
    """Generate Verilog for instruction decoder."""
    decoder_type = params['decoder_type']
    if decoder_type == 'hardwired':
        template = """
module decoder_hardwired (
    input [31:0] instr,
    output reg [3:0] opcode,  // Simplified 4-bit opcode
    output reg [2:0] dest_reg,
    output reg [2:0] src1_reg,
    output reg [3:0] mode,  // Addressing mode
    output reg [13:0] imm  // Immediate
);
    // Hardwired decoding logic
    always @(*) begin
        opcode = instr[31:28];
        dest_reg = instr[27:25];
        src1_reg = instr[24:22];
        mode = instr[21:18];
        imm = instr[17:4];
    end
endmodule
"""
    else:  # microcoded
        template = """
module decoder_microcoded (
    input [31:0] instr,
    input clk,
    output reg [15:0] micro_addr,  // Microcode address
    output reg micro_we
);
    // Simple microcode ROM (generated separately)
    reg [31:0] micro_rom [0:255];  // 256 entries, 32-bit microinstructions
    
    initial begin
        // Microcode initialization would be populated by generator
        // For now, placeholder
        micro_rom[0] = 32'hDEADBEEF;  // Example
    end
    
    always @(*) begin
        // Decode to micro-op address
        micro_addr = instr[15:0];  // Simplified
        micro_we = 1'b0;
    end
endmodule
"""
    return template

def generate_alu_verilog(params: Dict[str, Any]) -> str:
    """Generate Verilog for ALU."""
    exec_units = params['exec_units']
    if exec_units == 'single_alu':
        template = """
module alu (
    input [3:0] op,
    input [63:0] a, b,
    output reg [63:0] result,
    output reg zero_flag
);
    always @(*) begin
        case (op)
            4'h1: result = a + b;  // ADD
            4'h2: result = a - b;  // SUB
            4'h3: result = a & b;  // AND
            4'h4: result = a | b;  // OR
            4'h5: result = a ^ b;  // XOR
            default: result = a;
        endcase
        zero_flag = (result == 64'h0);
    end
endmodule
"""
    else:  # separate_agu_alu
        template = """
module agu_alu_separate (
    input [3:0] op,
    input [63:0] a, b,
    input is_memory_op,
    output reg [63:0] result,
    output reg [63:0] addr_calc,
    output reg zero_flag
);
    // ALU part
    always @(*) begin
        if (is_memory_op) begin
            addr_calc = a + b;  // Address generation
            result = 64'h0;
        end else begin
            case (op)
                4'h1: result = a + b;
                // ... other ops
                default: result = a;
            endcase
            addr_calc = 64'h0;
        end
        zero_flag = (result == 64'h0);
    end
endmodule
"""
    return template

def generate_memory_interface_verilog(params: Dict[str, Any]) -> str:
    """Generate Verilog for memory interface."""
    memory_type = params['memory_type']
    if memory_type == 'simple':
        template = """
module memory_simple (
    input clk,
    input [63:0] addr,
    input [63:0] wdata,
    input we,
    output reg [63:0] rdata
);
    reg [63:0] mem [0:1023];  // Small memory 1KB
    
    always @(posedge clk) begin
        if (we) begin
            mem[addr[9:0]] <= wdata;  // Simplified addressing
        end
        rdata <= mem[addr[9:0]];
    end
endmodule
"""
    else:  # cached
        template = """
module memory_cached (
    input clk,
    input [63:0] addr,
    input [63:0] wdata,
    input we,
    output reg [63:0] rdata,
    output reg hit
);
    // Simple direct-mapped I-cache, 16 entries, 4 words each
    reg [63:0] cache_data [0:15][0:3];
    reg [63:0] cache_tags [0:15];
    reg [3:0] valid [0:15];
    
    // Simplified cache logic (placeholder)
    always @(*) begin
        // Cache hit/miss logic here
        hit = 1'b1;  // Assume hit for simplicity
        rdata = cache_data[addr[7:4]][addr[3:2]];
    end
endmodule
"""
    return template

def generate_top_level_verilog(params: Dict[str, Any], output_dir: str = '.') -> str:
    """Generate top-level Verilog module."""
    num_regs = params['num_regs']
    pipeline_depth = params['pipeline_depth']
    reg_names = MicroX86Params.REG_NAMES[:num_regs]
    
    # Include other modules
    verilog_parts = [
        generate_register_file_verilog(params),
        generate_decoder_verilog(params),
        generate_alu_verilog(params),
        generate_memory_interface_verilog(params)
    ]
    
    top_template = f"""
// Top-level micro-x86-64 core
// Parameters: {{params}}

{{chr(10).join(verilog_parts)}}

module micro_x86_core #(
    parameter NUM_REGS = {num_regs},
    parameter PIPELINE_DEPTH = {pipeline_depth}
)(
    input clk,
    input reset,
    input [31:0] instr,  // From fetch stage
    output [63:0] pc_out
);

    wire [63:0] rdata1, rdata2;
    wire [3:0] opcode;
    wire [2:0] dest_reg, src1_reg;
    wire [3:0] mode;
    wire [13:0] imm;
    wire [63:0] alu_result;
    wire zero_flag;
    
    // Instantiate components based on params
    reg_file #(.NUM_REGS(NUM_REGS)) rf (
        .clk(clk),
        .we(/* from control */),
        .waddr(dest_reg),
        .raddr1(src1_reg),
        .raddr2(/* src2 */),
        .wdata(alu_result),
        .rdata1(rdata1),
        .rdata2(rdata2)
    );
    
    decoder_{params['decoder_type']} dec (
        .instr(instr),
        .opcode(opcode),
        .dest_reg(dest_reg),
        .src1_reg(src1_reg),
        .mode(mode),
        .imm(imm)
    );
    
    alu alu_inst (
        .op(opcode[3:0]),
        .a(rdata1),
        .b(/* src2 or imm */),
        .result(alu_result),
        .zero_flag(zero_flag)
    );
    
    memory_{params['memory_type']} mem_inst (
        .clk(clk),
        .addr(/* effective addr */),
        .wdata(rdata1),
        .we(/* control */),
        .rdata(/* to reg */)
    );
    
    // Pipeline registers for {{pipeline_depth}} stages (simplified)
    reg [63:0] pipeline_regs [{pipeline_depth}][/* width */];
    
    // PC logic
    reg [63:0] pc;
    always @(posedge clk) begin
        if (reset) pc <= 64'h0;
        else pc <= pc + 32'd4;  // Assume 32-bit instr
    end
    assign pc_out = pc;
    
    // Register names for simulation: {', '.join(reg_names)}
    
endmodule
"""
    
    filename = os.path.join(output_dir, f"micro_x86_core_{hashlib.md5(str(params).encode()).hexdigest()[:8]}.v")
    with open(filename, 'w') as f:
        f.write(top_template)
    print(f"Generated Verilog: {filename}")
    return filename

def similarity_search(seeds: List[str], query_words: List[str], max_results: int = 5) -> List[Tuple[str, float]]:
    """Phase 3: Similarity search using lexicon."""
    target_params = {}
    for word in query_words:
        if word in MicroX86Params.LEXICON:
            for k, v in MicroX86Params.LEXICON[word].items():
                target_params[k] = v
    
    results = []
    for seed in seeds:
        gen_params = seed_to_params(seed)
        # Simple Euclidean distance on params (simplified)
        distance = 0.0
        for k in target_params:
            if k in gen_params:
                # Normalize and compute diff (placeholder)
                distance += abs(hash(str(gen_params[k])) % 100 - hash(str(target_params[k])) % 100)
        results.append((seed, distance))
    
    results.sort(key=lambda x: x[1])
    return results[:max_results]

def verify_verilog(verilog_file: str) -> bool:
    """Phase 4: Basic verification with Yosys and Verilator stubs."""
    try:
        # Syntax check with Yosys
        subprocess.run(['yosys', '-p', f'read_verilog {verilog_file}; hierarchy -check;'], 
                       check=True, capture_output=True)
        print("Syntax check passed.")
        
        # Synthesis size estimate
        synth_cmd = f'yosys -p "read_verilog {verilog_file}; synth -top micro_x86_core; abc; stat"'
        result = subprocess.run(synth_cmd, shell=True, capture_output=True, text=True)
        print("Synthesis:", result.stdout)
        if "Error" in result.stderr:
            return False
        
        # Simulation stub (requires test program)
        # subprocess.run(['verilator', '--cc', verilog_file, '--exe', 'test.cpp'], check=True)
        print("Simulation stub: Would run Verilator here.")
        return True
    except subprocess.CalledProcessError:
        print("Verification failed.")
        return False

def generate_assembler(params: Dict[str, Any]) -> str:
    """Generate simple assembler for micro-x86-64."""
    # Placeholder assembler logic
    assembler_code = """
# Simple assembler placeholder
# Input: assembly text, Output: binary instructions
def assemble(line):
    # Parse MOV RAX, 10 -> encode to 32-bit instr
    return 0xDEADBEEF  # Placeholder
"""
    return assembler_code

def main():
    if len(sys.argv) < 2:
        print("Usage: python cpu_babel_generator.py <seed> [query_words...]")
        sys.exit(1)
    
    seed = sys.argv[1]
    query_words = sys.argv[2:] if len(sys.argv) > 2 else []
    
    params = seed_to_params(seed)
    print("Generated params:", params)
    
    verilog_file = generate_top_level_verilog(params)
    
    if query_words:
        # Example seeds for search
        example_seeds = [f"seed_{i}" for i in range(10)]
        matches = similarity_search(example_seeds, query_words)
        print("Search results:", matches)
    
    verify = verify_verilog(verilog_file)
    if verify:
        print("Core verified successfully.")
    
    # Generate assembler
    with open('assembler.py', 'w') as f:
        f.write(generate_assembler(params))
    print("Assembler generated: assembler.py")

if __name__ == "__main__":
    main()
