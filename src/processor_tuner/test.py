import re
def find_patterns(text):
    # Define a regular expression pattern
    # This pattern will capture instances of the base string followed by any valid suffix and '++'
    pattern = r'new freechips\.rocketchip\.rocket\.\w+\s*\+\+'
    
    # Find all matches of the pattern in the text
    matches = re.findall(pattern, text)
    return matches

# Example usage
text = """
new freechips.rocketchip.rocket.WithFastMulDiv ++ 
new freechips.rocketchip.rocket.WithNoBtb ++
new freechips.rocketchip.rocket.WithNoBtb ++
"""
result = find_patterns(text)
print(result)  # Output: List of found patterns