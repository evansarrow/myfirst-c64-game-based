import sys
import os

# C64 BASIC V2 Token Mapping
# Ordered by length descending to prevent substring mismatch (e.g. PRINT# vs PRINT)
TOKENS_LIST = [
    ("INPUT#", 132), ("PRINT#", 152), ("RIGHT$", 201),
    ("LEFT$", 200), ("RESTORE", 140), ("RETURN", 142),
    ("STATUS", 185), ("INPUT", 133), ("PRINT", 153),
    ("GOSUB", 141), ("WRITE", 152), ("PEEK", 194),
    ("STR$", 196), ("MID$", 202), ("STEP", 169),
    ("STOP", 144), ("WAIT", 146), ("LOAD", 147),
    ("SAVE", 148), ("VERIFY", 149), ("POKE", 151),
    ("CONT", 154), ("LIST", 155), ("OPEN", 159),
    ("CLOSE", 160), ("TAB(", 163), ("SPC(", 166),
    ("THEN", 167), ("SGN", 180), ("INT", 181),
    ("ABS", 182), ("USR", 183), ("FRE", 184),
    ("POS", 185), ("SQR", 186), ("RND", 187),
    ("LOG", 188), ("EXP", 189), ("COS", 190),
    ("SIN", 191), ("TAN", 192), ("LEN", 195),
    ("VAL", 197), ("ASC", 198), ("CHR$", 199),
    ("ATN", 193), ("END", 128), ("FOR", 129),
    ("NEXT", 130), ("DATA", 131), ("DIM", 134),
    ("READ", 135), ("LET", 136), ("GOTO", 137),
    ("RUN", 138), ("IF", 139), ("REM", 143),
    ("ON", 145), ("DEF", 150), ("CLR", 156),
    ("CMD", 157), ("SYS", 158), ("GET", 161),
    ("NEW", 162), ("TO", 164), ("FN", 165),
    ("NOT", 168), ("AND", 175), ("OR", 176),
    ("+", 170), ("-", 171), ("*", 172), ("/", 173),
    ("^", 174), (">", 177), ("=", 178), ("<", 179)
]

def compile_basic(input_file, output_file):
    print(f"Compiling {input_file} to {output_file}...")
    
    if not os.path.exists(input_file):
        print(f"Error: Source file {input_file} does not exist.")
        sys.exit(1)
        
    with open(input_file, "r") as f:
        lines = f.readlines()
        
    compiled_lines = []
    
    for raw_line in lines:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
            
        # Extract line number
        parts = raw_line.split(" ", 1)
        if not parts[0].isdigit():
            print(f"Skipping line without line number: {raw_line}")
            continue
            
        line_num = int(parts[0])
        line_content = parts[1] if len(parts) > 1 else ""
        
        # Tokenize content
        tokenized = bytearray()
        i = 0
        in_quotes = False
        in_rem = False
        in_data = False
        
        while i < len(line_content):
            char = line_content[i]
            
            # Handle quotes
            if char == '"':
                in_quotes = not in_quotes
                tokenized.append(ord(char))
                i += 1
                continue
                
            # If inside quotes or a REM statement, do not tokenize
            if in_quotes or in_rem:
                tokenized.append(ord(char))
                i += 1
                continue

            # If inside DATA statement, store literally (except colon starts new statement)
            if in_data:
                if char == ':':
                    in_data = False
                    tokenized.append(ord(char))
                    i += 1
                else:
                    val = ord(char)
                    if 'a' <= char <= 'z':
                        val = ord(char.upper())
                    tokenized.append(val)
                    i += 1
                continue
                
            # Check for keyword matches
            matched = False
            for keyword, token_byte in TOKENS_LIST:
                length = len(keyword)
                if line_content[i:i+length].upper() == keyword:
                    tokenized.append(token_byte)
                    i += length
                    matched = True
                    # If we matched REM, everything until the end of line is a comment
                    if keyword == "REM":
                        in_rem = True
                    # If we matched DATA, store rest literally until colon
                    if keyword == "DATA":
                        in_data = True
                    break
                    
            if not matched:
                val = ord(char)
                if 'a' <= char <= 'z':
                    val = ord(char.upper())
                tokenized.append(val)
                i += 1
                
        compiled_lines.append((line_num, tokenized))
        
    # Build the binary data
    # Standard load address for BASIC: 2049 ($0801)
    load_addr = 2049
    binary_data = bytearray()
    
    # First 2 bytes of PRG is the load address
    binary_data.append(load_addr & 255)
    binary_data.append((load_addr >> 8) & 255)
    
    current_addr = load_addr
    
    for idx, (line_num, token_bytes) in enumerate(compiled_lines):
        # Line layout:
        # 2 bytes next line address pointer
        # 2 bytes line number
        # N bytes tokenized content
        # 1 byte null terminator
        line_len = 2 + 2 + len(token_bytes) + 1
        next_addr = current_addr + line_len
        
        line_data = bytearray()
        # Next line pointer
        line_data.append(next_addr & 255)
        line_data.append((next_addr >> 8) & 255)
        # Line number
        line_data.append(line_num & 255)
        line_data.append((line_num >> 8) & 255)
        # Content
        line_data.extend(token_bytes)
        # Null terminator
        line_data.append(0)
        
        binary_data.extend(line_data)
        current_addr = next_addr
        
    # Program end marker: two null bytes for next line pointer
    binary_data.append(0)
    binary_data.append(0)
    
    with open(output_file, "wb") as f:
        f.write(binary_data)
        
    print(f"Successfully compiled to {output_file}! Size: {len(binary_data)} bytes.")

if __name__ == "__main__":
    infile = "space_dodge.bas"
    outfile = "space_dodge.prg"
    if len(sys.argv) > 1:
        infile = sys.argv[1]
    if len(sys.argv) > 2:
        outfile = sys.argv[2]
    compile_basic(infile, outfile)
