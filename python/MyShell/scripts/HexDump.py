import sys
import os

def hex_dump(data, bytes_per_line=16):
    output_lines = []
    
    for offset in range(0, len(data), bytes_per_line):
        chunk = data[offset:offset + bytes_per_line]
        
        hex_bytes = " ".join(f"{b:02X}" for b in chunk)
        padding = "   " * (bytes_per_line - len(chunk))
        ascii_text = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        output_lines.append(f"{offset:08X}  {hex_bytes}{padding}  |{ascii_text}|")
        
    return "\n".join(output_lines)

def main():
    data = b""

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.isfile(file_path):
            print(f"HexDump error: File '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception as e:
            print(f"HexDump error: {e}", file=sys.stderr)
            sys.exit(1)

    elif not sys.stdin.isatty():
        data = sys.stdin.buffer.read()
    else:
        print("Usage: HexDump.py <file_path> OR command | HexDump.py")
        sys.exit(1)

    if data:
        print(hex_dump(data))

if __name__ == "__main__":
    main()