import base64
import urllib.parse

def decode_bing_url(u_param):
    try:
        # Remove 'a1' prefix if present
        if u_param.startswith("a1"):
            u_param = u_param[2:]
        
        # Add padding if needed
        u_param += "=" * ((4 - len(u_param) % 4) % 4)
        
        # Decode
        decoded_bytes = base64.urlsafe_b64decode(u_param)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

# Examples from log
examples = [
    "a1aHR0cHM6Ly93d3cuZmx1dG1hdGUuaW4vcGctaW4tYWhtZWRhYmFk", 
    "a1aHR0cHM6Ly9rcmlwYWxob21lcy5jb20v",
    "a1aHR0cHM6Ly93d3cubWFnaWNicmlja3MuY29tL3BnLXdpdGgtZm9vZC1pbi1haG1lZGFiYWQtcHBwZLI" # Modified slightly to simulate real
]

# Real ones from log:
# u=a1aHR0cHM6Ly93d3cuZmxhdG1hdGUuaW4vcGctaW4tYWhtZWRhYmFk
# u=a1aHR0cHM6Ly9rcmlwYWxob21lcy5jb20v
# u=a1aHR0cHM6Ly93d3cubWFnaWNicmlja3MuY29tL3BnLXdpdGgtZm9vZC1pbi1haG1lZGFiYWQtcHBwZnI 
# (Note: I need to be careful with copying from the truncated log 
# The log had newlines, I will try to reconstruct one manually or just test the logic)

real_u = "a1aHR0cHM6Ly93d3cuZmxhdG1hdGUuaW4vcGctaW4tYWhtZWRhYmFk" 
print(f"Decoded {real_u}: {decode_bing_url(real_u)}")

real_u2 = "a1aHR0cHM6Ly9rcmlwYWxob21lcy5jb20v"
print(f"Decoded {real_u2}: {decode_bing_url(real_u2)}")
